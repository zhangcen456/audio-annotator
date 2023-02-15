#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/9/4 5:16 PM
# @Author  : vell
# @Email   : vellhe@tencent.com
import json
import logging
import os

from server.base import BaseReqHandler
from server.file_utils import list_files, get_relative_path, find_child_path_by_re, list_files_mul

logger = logging.getLogger(__name__)


class GetTask(BaseReqHandler):
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)
        self.wav_dir = application.settings["settings"]["wav_dir"]
        print(application.settings)

    def _get_task(self, tmp_wavs_key="all", wav_suffix=".wav", review=False):
        # if tmp_wavs_key not in self.application.settings:
        if True:
            self.application.settings[tmp_wavs_key] = list_files_mul(self.wav_dir, wav_suffix)

        if not self.application.settings[tmp_wavs_key]:
            del self.application.settings[tmp_wavs_key]
            return None

        for wav_path in self.application.settings[tmp_wavs_key][:]:
            if review:
                # 如果需要从新review，就不管json 是否存在
                self.application.settings[tmp_wavs_key].remove(wav_path)
                return wav_path
            else:
                wav_json_path = wav_path + ".json"
                if os.path.exists(wav_json_path) and os.path.getsize(wav_json_path) > 0:
                    self.application.settings[tmp_wavs_key].remove(wav_path)
                else:
                    return wav_path
        return None

    def get(self):
        review = self.get_argument('review', default="true")
        wav_name = self.get_argument('wav_name', default=".wav,.mp3")
        user_id = self.get_argument("user_id", default="all")

        tmp_wavs_key = user_id + wav_name
        wav_path = self._get_task(tmp_wavs_key=tmp_wavs_key, wav_suffix=wav_name, review=(review == "true"))
        resp = dict()
        if not wav_path:
            # 没有wav了
            resp["ret"] = "no_tasks"
        else:
            resp["ret"] = "ok"

            annotations = []
            wav_json_path = wav_path + ".json"
            record_path=wav_path+".record"
            if os.path.exists(wav_json_path) and os.path.getsize(wav_json_path) > 0:
                annotation_dump(wav_json_path,record_path)
                with open(wav_json_path, encoding="utf-8") as f:
                    task_ret = json.load(f)
                    annotations = task_ret["annotations"]

            wavText=''
            wav_text_path = wav_path + ".txt"
            if os.path.exists(wav_text_path) and os.path.getsize(wav_text_path) > 0:
                with open(wav_text_path,encoding='utf-8') as f:
                    lines=[line.strip() for line in f]
                wavText="||".join(lines)

            rel_wav_path = get_relative_path(self.wav_dir, wav_path)
            url = os.path.join("/wavs", rel_wav_path)
            resp["task"] = {
                "feedback": "none",
                "visualization": "waveform",
                "proximityTag": [],
                "annotationTag": [
                    "人说话声",
                    "突发噪音"
                ],
                "url": url,
                "tutorialVideoURL": "",
                "alwaysShowTags": True,
                "annotations": annotations,
                "wavText":wavText
            }
        self.write(json.dumps(resp))

def annotation_dump(json_file,record_path):
    with open(json_file,'r+',encoding="utf-8") as f:
        records=json.load(f)
    if(len(records['annotations'])>10):
        annos=records['annotations']
        with open(record_path,"a") as f:
            save_annos=annos[:-10]
            for anno in save_annos:
                json.dump(anno,f)
                f.write("\n")
        records['annotations']=annos[-10:]
    with open(json_file,'w+',encoding="utf-8") as f:
        json.dump(records,f)