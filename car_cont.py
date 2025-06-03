#car1
import numpy as np

comu = np.array([0, 1, 1, 1, 0]).reshape(1, -1)  # 1行5列
comu=comu.T  # 转置为5行1列

def wanted_pos(x=[]):#使用动补数据中的car_x_positions
    x = np.array(x).reshape(1, -1)  # 确保x是一个行向量
    return ((x@comu)[0, 0])/3  # 返回第一个元素



#car2
import numpy as np
comu = np.array([0, 0, 1, 1, 1]).reshape(1, -1)  # 1行5列
comu = comu.T  # 转置为5行1列

def wanted_pos(x=[]):  #使用动补数据中的car_x_positions
    x = np.array(x).reshape(1, -1)  # 确保x是一个行向量
    return ((x @ comu)[0, 0]) / 3  # 返回第一个元素

#car3
import numpy as np
comu = np.array([1, 1, 0, 1, 0]).reshape(1, -1)  # 1行5列
comu = comu.T  # 转置为5行1列


def wanted_pos(x=[]):  #使用动补数据中的car_x_positions
    x = np.array(x).reshape(1, -1)  # 确保x是一个行向量
    return ((x @ comu)[0, 0]) / 3  # 返回第一个元素

#car4
import numpy as np
comu = np.array([0, 1, 1, 0, 1]).reshape(1, -1)  # 1行5列
comu = comu.T  # 转置为5行1列


def wanted_pos(x=[]):  #使用动补数据中的car_x_positions
    x = np.array(x).reshape(1, -1)  # 确保x是一个行向量
    return ((x @ comu)[0, 0]) / 3  # 返回第一个元素

#car5
import numpy as np
comu = np.array([1, 0, 1, 1, 0]).reshape(1, -1)  # 1行5列
comu = comu.T  # 转置为5行1列


def wanted_pos(x=[]):  #使用动补数据中的car_x_positions
    x = np.array(x).reshape(1, -1)  # 确保x是一个行向量
    return ((x @ comu)[0, 0]) / 3  # 返回第一个元素
