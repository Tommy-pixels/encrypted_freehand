#coding=utf-8
'''
    自动化引擎
        内容图 清洗 筛选 并上传
'''
from freehand.utils import globalTools
from freehand.contrib.poster.old_datapool import poster_img as Poster
from freehand.middleware.handler.img_handler import classifier as Classifier
from freehand.middleware.handler.img_handler import processing as Processing
from freehand.middleware.filter import image_mid as Filter
from freehand.contrib.db.db_singleton_connector.db_connector_shujuchi import DB_Singleton_DEFAULT
from freehand.utils.common import Controler_Time, Controler_Dir
from freehand.contrib.downloader import Downloader

def run(proj_absPath, origin, database, tableNameList, maskFilt=False):
    updateTime = Controler_Time.getCurDate("%Y%m%d")
    setting = {
        # 爬取下来的图片的存放路径
        'imgsCrawledDir': proj_absPath + '\\assets\imgsCrawled\\' + updateTime + '\\' + origin + '\\',
        # 经过百度识别重命名后存放的目录路径
        'imgsReconizedDir': proj_absPath + '\\assets\imgsReconized\\' + updateTime + '\\' + origin + '\\',
        # 初步处理过后的无水印的图片的目录
        'imgsDirDontHasWaterMask': proj_absPath + '\\assets\imgsDontHasWaterMask\\' + updateTime + '\\' + origin + '\\',
        # 初步处理过后有水印的图片的目录
        'imgsDirHasWaterMask': proj_absPath + '\\assets\imgDirHasWaterMask\\' + updateTime + '\\' + origin + '\\',
        # 处理完成的图片目录
        'imgsCleanedDir': proj_absPath + '\\assets\imgsCleanedDir\\' + updateTime + '\\' + origin + '\\',
        # 缩略图保存位置图片目录
        'imgsThumbnailDir': proj_absPath + '\\assets\imgsThumbnailDir\\' + updateTime + '\\' + origin + '\\',
    }

    # 判断配置里的目录是否存在，不存在则创建对应目录
    for item in setting.values():
        Controler_Dir.checkACreateDir(item)

    # 从数据库获取图片链接 下载图片
    print("从数据库获取图片链接")
    param = {
        'USER': 'root',
        'DBNAME': database,
        'PASSWORD': 'root',
        'HOST': '',
        'PORT': '',
    }
    dbOperator = DB_Singleton_DEFAULT()
    # 上传过的图片去重
    picList_posted_ = dbOperator.getAllDataFromDB("SELECT `origin_pic_path` FROM `postedurldatabase`.`tb_contentimgs_posted`")
    picList_posted = []
    for item in picList_posted_:
        picList_posted.append(item[0])
    print(picList_posted)
    print("下面开始下载图片")
    for table in tableNameList:
        sql = "SELECT `id`,`origin_pic_path` FROM `" + table + "`;"
        imgUrlPathList = dbOperator.getAllDataFromDB(sql)
        print("数据表为 ", table, "获得图片链接数量： ", len(imgUrlPathList))
        for imgUrl in imgUrlPathList:
            if (imgUrl[1] in picList_posted):
                continue
            imgName = table + "_" + str(imgUrl[0])
            Downloader.download_img(urlpath=imgUrl[1], imgname=imgName, dstDirPath=setting["imgsCrawledDir"])
            insert_SQL = "INSERT INTO `postedurldatabase`.`tb_contentimgs_posted` (`origin_pic_path`) VALUES (\'{}\');".format(
                imgUrl[1])
            dbOperator.insertData2DB(insert_SQL)

    print("图片下载完成")

    # 对爬取下来的图片进行处理 - 识别重命名、过滤、水印的识别及裁切 处理完后放在路径  ./assets/imgsCleanedDir 下
    # 2 重命名
    classifier = Classifier.imgsClassifier(crawledDirPath=setting['imgsCrawledDir'], savedDirPath=setting['imgsReconizedDir'])
    classifier.run()

    # 3 过滤 (关键词过滤、空文件过滤、水印识别及处理）
    print("下面开始过滤操作")
    if(maskFilt):
        filter = Filter.imgsFilter(
            imgsDontHasWaterMaskDir=setting['imgsDirDontHasWaterMask'],
            imgDirHasWaterMask=setting['imgsDirHasWaterMask'],
            imgCleanedStep1=setting['imgsCleanedDir'],
            dirOriPath=setting['imgsReconizedDir']
            # dirOriPath=setting['imgsCrawledDir']
        )
        print("有水印处理的过滤操作")
        filter.run_hasmaskOp()  # 这里再做一下优化
        # 处理网的水印图片位置分别在  imgsDirDontHasWaterMask 和 imgsDirHasWaterMask
        print("过滤操作完成")

        # 4 resize指定目录下的图片 默认为宽度小1000
        setImgSizer0 = Processing.ImgsSetSize(setting['imgsDirDontHasWaterMask'])
        setImgSizer0.resize_byDir()
        setImgSizer1 = Processing.ImgsSetSize(setting['imgsDirHasWaterMask'])
        setImgSizer1.resize_byDir()

        # 5 创建图片发送的poster 传送处理完成的图片
        # 传送内容图
        imgposter0 = Poster.Poster_Imgs_Contentimgs(imgDirPath=setting['imgsDirDontHasWaterMask'])
        imgposter0.post_auto('内容图')
        imgposter1 = Poster.Poster_Imgs_Contentimgs(imgDirPath=setting['imgsDirHasWaterMask'])
        imgposter1.post_auto('内容图')
    else:
        filter = Filter.imgsFilter(
            imgsDontHasWaterMaskDir=setting['imgsDirDontHasWaterMask'],
            imgDirHasWaterMask=setting['imgsDirHasWaterMask'],
            imgCleanedStep1=setting['imgsCleanedDir'],
            dirOriPath=setting['imgsReconizedDir']
            # dirOriPath=setting['imgsCrawledDir']
        )
        print("无水印处理的过滤操作")
        filter.run_nomaskOp()
        print("过滤操作完成")
        # 4 resize指定目录下的图片 默认为宽度小1000
        setImgSizer = Processing.ImgsSetSize(setting['imgsCleanedDir'])
        setImgSizer.resize_byDir()

        # 5 创建图片发送的poster 传送处理完成的图片
        # 传送内容图
        imgposter0 = Poster.Poster_Imgs_Contentimgs(imgDirPath=setting['imgsCleanedDir'])
        imgposter0.post_auto('内容图')

    globalTools.finishTask()
