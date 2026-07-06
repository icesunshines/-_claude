import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))
import traceback
from preprocessing import BLOOD_SUGAR_COL_MAPPING

try:
    import pandas as pd
    import numpy as np
    from preprocessing import load_pipeline, BLOOD_SUGAR_COL_MAPPING
    from predict import predict_blood_sugar

    pipeline = load_pipeline('blood_sugar')
    print("Pipeline loaded. feature_cols:", len(pipeline.feature_cols))

    request = {
        '性别': '女', '年龄': 45,
        '天门冬氨酸氨基转换酶': 20, '丙氨酸氨基转换酶': 25,
        '碱性磷酸酶': 80, 'r_谷氨酰基转换酶': 20,
        '总蛋白': 72, '白蛋白': 45, '球蛋白': 27, '白球比例': 1.67,
        '甘油三酯': 1.5, '总胆固醇': 5.0, '高密度脂蛋白胆固醇': 1.4,
        '低密度脂蛋白胆固醇': 3.2, '尿素': 5.0, '肌酐': 65, '尿酸': 300,
        '白细胞计数': 6.5, '红细胞计数': 4.5, '血红蛋白': 130,
        '红细胞压积': 0.39, '红细胞平均体积': 87, '红细胞平均血红蛋白量': 29,
        '红细胞平均血红蛋白浓度': 333, '红细胞体积分布宽度': 13.5,
        '血小板计数': 200, '血小板平均体积': 10, '血小板体积分布宽度': 12,
        '血小板比积': 0.2
    }

    result = predict_blood_sugar(request)
    print("Result:", result)
except Exception as e:
    traceback.print_exc()
