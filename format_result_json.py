# -*- coding:utf-8 -*-
import json

CONF_THD = 20 # 置信度门槛值
INTERVAL = 50  # 时间合并分块的间隔，0表示不进行合并分块，单位秒
PRE_TIME = 1
AFTER_TIME = 1

attr = {0:'敏感人物',#0: '涉政',
        1: '暴力',
        2: '黄色',
        3:'明星',
        4:'汽车',
        5:'物品',
        6:'场景',}

mapping = { 'car': '车辆',
            'celebrity': '明星',
            'scene': '场景',
            'tag_scene_info': '场景标签',
            'com_objects': '通用物品',
            'accu_objects': '精确物品',
            'obj_info': '物品信息',
            'porn': '色情',
            'politician': '敏感人物',
            'terror': '暴恐',
            }


def format_confidence(*args):
    zxd = sum(args)/len(args)
    return int(zxd*100) if zxd < 1 else int(round(zxd))


def s_to_hms(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "%02d:%02d:%02d" % (h, m, s)


def block_by_duration(name_summery):
    '''
    分块
    '''
    name_section = []
    name_combin = []
    i = 0
    p = 0
    l = len(name_summery)
    while i < l - 1:
        if name_summery[i + 1][2] - name_summery[i][3] > INTERVAL:
            name_section.append(list(name_summery[p:i + 1]))
            p = i + 1
        i += 1
    name_section.append(list(name_summery[p:]))

    for bl in name_section:
        name_block = [bl[0][0], bl[0][1], bl[0][2], bl[-1][3], len(bl), format_confidence(*[i[-1] for i in bl])]
        name_combin.append(name_block)

    return name_combin


def format_result_json(input_json, output_json):
    '''
        input_json:要转成xlsx的json文件
        output_xlsx:输出xlsx的路径
    '''
    summery_list = format_json_result_add_tag(input_json)
    set_summery_list = [list(set([i[1] for i in li])) for li in summery_list]

    combin_list = {}
    combin_list['celebrity'] = {}
    # try:
    for summery, set_summery in zip(summery_list, set_summery_list):
        for s in set_summery:
            temp = [it for it in summery if it[1] == s]
            temp_combin = block_by_duration(temp)
            temp_list = [[s_to_hms(i[2]-PRE_TIME), s_to_hms(i[3]+AFTER_TIME), i[4], (i[4]*i[4])/(i[3]-i[2]+1)]for i in temp_combin if abs(i[2]-i[3])>=10]
            temp_list.sort(key=lambda x:x[3], reverse=True)
            temp_list = [i[:3] for i in temp_list]
            if len(temp_list) > 0:
                tag = temp_combin[0][0]
                combin_list[tag][s] = temp_list
    with open(output_json, 'w', encoding='utf-8') as f:
        f.write(json.dumps(combin_list, ensure_ascii=False, indent=2))

    return True


def format_json_result_add_tag(json_file):
    star_summery = []

    with open(json_file,encoding="utf-8") as h:
        res = h.read()
        results = eval(res)['results']
        for v in results:
            """
            "celebrity": [], "scene": [], "tag_scene_info": [], "com_objects": [], "accu_objects": [], "obj_info": []}
            """
            begin = round(v['time_from_start'])
            res = v.get('result', {})
            if res.get("celebrity"):
                star_info_list = res['celebrity']
                for object_info in star_info_list:
                    conf = object_info.get('confidence') or object_info.get("conf")
                    conf = int(conf*100) if conf < 1 else int(round(conf))
                    if conf > CONF_THD:
                        # end = (begin + int(object_info['duration']))
                        duration = round(float(object_info['duration']))
                        end = begin + duration
                        confidence = object_info.get('confidence') or object_info.get('conf')
                        confidence = int(confidence * 100) if confidence <= 1.0 else int(confidence)
                        result_item = [
                            "celebrity",  # 属性
                            object_info['name'],  # 内容
                            begin,  # 开始时间
                            end,  # 结束时间
                            object_info['duration'],  # 时长
                            confidence  # 置信度
                        ]
                        star_summery.append(result_item)

    return [star_summery]


if __name__ == '__main__':


    input_json = './100013.all.json'
    output_json = './100013_o.json'
    r = format_result_json(input_json, output_json)
