from jmcomic import *
from jmcomic.cl import JmcomicUI

# 下方填入你要下载的本子的id，一行一个，每行的首尾可以有空白字符
jm_albums = '''


1436526
1442074
1442235
1442595
594838
1442594
451610
1230347
1441240
1441503
1441900
1442605
1442470
1045423
479549
636717
479806
1435055
560401
1441966
1442432
1247541
1442231
1437869
1221887
90521
138039
542252
1088840
1045271
1242972
1215927
1434801
1439133
525223
1439123
1439559
1439552
1221763
1439840
1154472
1218346
1439855
1073194
346821
1198322
1216342
640712
626391
333696
1438978
1026850
13371
1059539
148624
530571
1386303
298716
1016871
1437322
1038310
1436220
149197
1226028
1232437
1058392
1230045
546194
1025331
1435339
1435753
1212643
1390405
1254368
224412
281451
384716
1246094
1058687
1156281
508253
487705
1049368
1137826
484683
474028
628595
542881
1433586
400438
1207813
1433222
1023592
1433212
625795
507769
579627
1154516
91109
378406
42465
57111
301670
198023
34377
620203
124135
226909
187420
441922
1243400
12060
24374
432
1432949
66683
297109
527941
1432919
77106
226647
1078526
62119
187
385529
456434
1238236
1038284
16388
25805
487286
475612
1102470
1429370
1429260
1430734
1430747
260915
368317
355659
1121637
1141345
1430177
1429565
448016
1164504
258414
1197584
1429697
1251204
1229553
1255621
1427430
1257204
480715
1428528
1428685
221219
637279
638098
648641
648642
650551
635848
1256743
1394768
1409399
1427453
1415940
564536
552848
165804
210661
124304
149105
1252539
1256762
1256578
1427812
209654
1390541
330028
1427425
1205789
1427523
1254780
615085
1084889
1425827
1239389
1246549
229859
149996
1121067
1195597
1423342
428432
1423220
1423345
1423561
620808
423745
1215962
1390470
279430
382552
1422195
1238473
377532
269408
1232169
534
1406375
1410417
1323910
535646
1363995
1371211
1332419
1336943
1165027
1191862
295686
533198
1258216
467180
1295258
1289626
1291838
1291836
626246
466388
1286009
255
152497
179106
485015
326315
626262
1019113
1096723
259194
143092
1084888
405524
1213695
330778
1238381
1255853
1256041
147905
1259136
445600
1221168
1258305
1258776
1259200
1258059
1255552
1256026
1247992
148753
466763
1255294
224502
1251414
386001
558836
609256
1249304
1243219
1248799
1142622
1228837
1240372
1229747
1199248
1193587
1060990
1246547
1248505
1216644
1198517
255776
431296
1207473
1204624
1201394
1175609

'''

# 单独下载章节
jm_photos = '''



'''


def env(name, default, trim=('[]', '""', "''")):
    import os
    value = os.getenv(name, None)
    if value is None or value == '':
        return default

    for pair in trim:
        if value.startswith(pair[0]) and value.endswith(pair[1]):
            value = value[1:-1]

    return value


def get_id_set(env_name, given):
    aid_set = set()
    for text in [
        given,
        (env(env_name, '')).replace('-', '\n'),
    ]:
        aid_set.update(str_to_set(text))

    return aid_set


def main():
    album_id_set = get_id_set('JM_ALBUM_IDS', jm_albums)
    photo_id_set = get_id_set('JM_PHOTO_IDS', jm_photos)

    helper = JmcomicUI()
    helper.album_id_list = list(album_id_set)
    helper.photo_id_list = list(photo_id_set)

    option = get_option()
    helper.run(option)
    option.call_all_plugin('after_download')


def get_option():
    # 读取 option 配置文件
    option = create_option(os.path.abspath(os.path.join(__file__, '../../assets/option/option_workflow_download.yml')))

    # 支持工作流覆盖配置文件的配置
    cover_option_config(option)

    # 把请求错误的html下载到文件，方便GitHub Actions下载查看日志
    log_before_raise()

    return option


def cover_option_config(option: JmOption):
    dir_rule = env('DIR_RULE', None)
    if dir_rule is not None:
        the_old = option.dir_rule
        the_new = DirRule(dir_rule, base_dir=the_old.base_dir)
        option.dir_rule = the_new

    impl = env('CLIENT_IMPL', None)
    if impl is not None:
        option.client.impl = impl

    suffix = env('IMAGE_SUFFIX', None)
    if suffix is not None:
        option.download.image.suffix = fix_suffix(suffix)

    pdf_option = env('PDF_OPTION', None)
    if pdf_option and pdf_option != '否':
        call_when = 'after_album' if pdf_option == '是 | 本子维度合并pdf' else 'after_photo'
        
        pdf_name_rule = env('PDF_NAME_RULE', None)
        if isinstance(pdf_name_rule, str):
            pdf_name_rule = pdf_name_rule.strip()
            
        if not pdf_name_rule:
            pdf_name_rule = '[JM{Aid}] {Atitle}' if call_when == 'after_album' else '[JM{Aid}] 第{Pindex}章-JM{Pid}-{Ptitle}'
            
        plugin = [{
            'plugin': Img2pdfPlugin.plugin_key,
            'kwargs': {
                'pdf_dir': option.dir_rule.base_dir + '/pdf/',
                'filename_rule': pdf_name_rule,
                'delete_original_file': True,
            }
        }]
        option.plugins[call_when] = plugin


def log_before_raise():
    jm_download_dir = env('JM_DOWNLOAD_DIR', workspace())
    mkdir_if_not_exists(jm_download_dir)

    def decide_filepath(e):
        resp = e.context.get(ExceptionTool.CONTEXT_KEY_RESP, None)

        if resp is None:
            suffix = str(time_stamp())
        else:
            suffix = resp.url

        name = '-'.join(
            fix_windir_name(it)
            for it in [
                e.description,
                current_thread().name,
                suffix
            ]
        )

        path = f'{jm_download_dir}/【出错了】{name}.log'
        return path

    def exception_listener(e: JmcomicException):
        """
        异常监听器，实现了在 GitHub Actions 下，把请求错误的信息下载到文件，方便调试和通知使用者
        """
        # 决定要写入的文件路径
        path = decide_filepath(e)

        # 准备内容
        content = [
            str(type(e)),
            e.msg,
        ]
        for k, v in e.context.items():
            content.append(f'{k}: {v}')

        # resp.text
        resp = e.context.get(ExceptionTool.CONTEXT_KEY_RESP, None)
        if resp:
            content.append(f'响应文本: {resp.text}')

        # 写文件
        write_text(path, '\n'.join(content))

    JmModuleConfig.register_exception_listener(JmcomicException, exception_listener)


if __name__ == '__main__':
    main()
