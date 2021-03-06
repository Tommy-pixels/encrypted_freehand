#coding=utf-8
'''
    自动化引擎
        缩略图 清洗 筛选 并上传
'''
from freehand.utils import globalTools
from freehand.contrib.poster.old_datapool import poster_img
from freehand.middleware.handler.img_handler import classifier as Classifier
from freehand.middleware.handler.img_handler import processing as Processing
from freehand.middleware.filter import image_mid
from freehand.contrib.db.db_notsingleton_connector.db_connector_default import DB_NotSingleton_DEFAULT
from freehand.utils.common import Controler_Time, Controler_Dir
from freehand.contrib.downloader import Downloader

def run(proj_absPath, origin, database, tableNameList):
    # 将目录下的图片图片传到接口
    # 获取当前目录所在绝对路径
    # proj_absPath = os.path.abspath(os.path.dirname(__file__))
    updateTime = Controler_Time.getCurDate("%Y%m%d")
    setting = {
        # 爬取下来的图片的存放路径
        'imgsCrawledDir' : proj_absPath + '\\assets\imgsCrawled\\' + updateTime + '\\' + origin + '\\',
        # 经过百度识别重命名后存放的目录路径
        'imgsReconizedDir': proj_absPath + '\\assets\imgsReconized\\' + updateTime + '\\' + origin + '\\',
        # 初步处理过后的无水印的图片的目录
        'imgsDirDontHasWaterMask' : proj_absPath + '\\assets\imgsDontHasWaterMask\\' + updateTime + '\\' + origin + '\\',
        # 初步处理过后有水印的图片的目录
        'imgsDirHasWaterMask' : proj_absPath + '\\assets\imgDirHasWaterMask\\' + updateTime + '\\' + origin + '\\',
        # 处理完成的图片目录
        'imgsCleanedDir' : proj_absPath + '\\assets\imgsCleanedDir\\' + updateTime + '\\' + origin + '\\',
        # 缩略图保存位置图片目录
        'imgsThumbnailDir' : proj_absPath + '\\assets\imgsThumbnailDir\\' + updateTime + '\\' + origin + '\\',
    }

    # 判断配置里的目录是否存在，不存在则创建对应目录
    for item in setting.values():
        Controler_Dir.checkACreateDir(item)

    # 从数据库获取图片链接 下载图片
    print("从数据库获取图片链接")
    db = DB_NotSingleton_DEFAULT()
    # 上传过的图片去重
    picList_posted_ = db.getAllDataFromDB("SELECT `origin_pic_path` FROM `postedurldatabase`.`tb_thumbnailimgs_posted`")
    picList_posted = []
    for item in picList_posted_:
        picList_posted.append(item[0])
    print(picList_posted)
    print("下面开始下载图片")
    for table in tableNameList:
        sql = "SELECT `id`,`origin_pic_path` FROM `" + table + "`;"
        imgUrlPathList = db.getAllDataFromDB(sql)
        print("数据表为 ", table, "获得图片链接数量： ", len(imgUrlPathList))
        for imgUrl in imgUrlPathList:
            if(imgUrl[1] in picList_posted):
                continue
            imgName = table + "_" + str(imgUrl[0])
            Downloader.download_img(urlpath=imgUrl[1], imgname=imgName, dstDirPath=setting["imgsCrawledDir"])
            insert_SQL = "INSERT INTO `postedurldatabase`.`tb_thumbnailimgs_posted` (`origin_pic_path`) VALUES (\'{}\');".format(imgUrl[1])
            db.insertData2DB(insert_SQL)

    print("图片下载完成")
    # 对爬取下来的图片进行处理 - 识别重命名、过滤、水印的识别及裁切 处理完后放在路径  ./assets/imgsCleanedDir 下
    # 2 重命名
    classifier = Classifier.imgsClassifier(crawledDirPath=setting['imgsCrawledDir'], savedDirPath=setting['imgsReconizedDir'])
    classifier.run()

    # 3 过滤 (关键词过滤、空文件过滤、水印识别及处理）
    print("下面开始过滤操作")
    filter = image_mid.imgsFilter(
        imgsDontHasWaterMaskDir=setting['imgsDirDontHasWaterMask'],
        imgDirHasWaterMask=setting['imgsDirHasWaterMask'],
        imgCleanedStep1 = setting['imgsCleanedDir'],
        # dirOriPath=setting['imgsReconizedDir']
        dirOriPath = setting['imgsCrawledDir']
    )
    filter.run_()    # 这里再做一下优化
    print("过滤操作完成")

    # 4 将过滤后的图片整成缩略图
    print("下面将图片整成缩略图")
    thumbnailOriDir = setting['imgsReconizedDir']
    thumbnailDstDir = setting['imgsThumbnailDir']
    imgprocesser = Processing.Imgs2ThumbnailByDir(thumbnailOriDirPath=thumbnailOriDir, thumbnailDstDirPath=thumbnailDstDir)
    imgprocesser.cutOff2ThumbnailByDir()

    print("下面将开始传送")
    # # 4 创建图片发送的poster 传送处理完成的图片
    # 传送缩略图
    imgposter0 = poster_img.Poster_Imgs_Thumbnails(imgDirPath=setting['imgsThumbnailDir'])
    imgposter0.post_auto('缩略图')
    globalTools.finishTask()
