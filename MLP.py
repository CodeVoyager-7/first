import time
import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, r2_score, mean_squared_error
from sklearn.model_selection import GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import MinMaxScaler
from xgboost import XGBRegressor
from scipy import stats

# 特征标准化
# 树模型（随机森林、ExtraTrees）一般不需要标准化，但为了稳健性可以保留。
# 考虑到追求误差最小，我们不使用标准化，保留原始数据特征，因为标准化有时会压缩特征方差。
# scaler_x = StandardScaler()
# scaler_y = StandardScaler()

# 加载数据集（请根据实际路径修改）
train_dataSet = pd.read_csv(r'C:\Users\ASUS\Desktop\ML期末代码比赛\加噪数据集\modified_数据集Time_Series661_detail.dat')
test_dataSet = pd.read_csv(r'C:\Users\ASUS\Desktop\ML期末代码比赛\加噪数据集\modified_数据集Time_Series662_detail.dat')


# columns表示原始列，noise_columns表示添加噪声的额列
columns = ['T_SONIC', 'CO2_density', 'CO2_density_fast_tmpr', 'H2O_density', 'H2O_sig_strgth', 'CO2_sig_strgth',]
noise_columns = ['Error_T_SONIC', 'Error_CO2_density', 'Error_CO2_density_fast_tmpr', 'Error_H2O_density',
                 'Error_H2O_sig_strgth', 'Error_CO2_sig_strgth']

CL = ['T_SONIC', 'CO2_density', 'CO2_density_fast_tmpr', 'H2O_density', 'H2O_sig_strgth', 'CO2_sig_strgth','Error_T_SONIC', 'Error_CO2_density', 'Error_CO2_density_fast_tmpr', 'Error_H2O_density',
                 'Error_H2O_sig_strgth', 'Error_CO2_sig_strgth']

## 查看数据缺失情况
data = train_dataSet[CL]
missingDf=data.isnull().sum().sort_values(ascending=False).reset_index()
missingDf.columns=['feature','miss_num']
missingDf['miss_percentage']=missingDf['miss_num']/data.shape[0]  #缺失值比例
print("缺失值比例")
print(missingDf)


# 初始化一个字典来存储每一列的异常值比例
outlier_ratios = {}

# 遍历每一列
for column in CL:
    # 计算每一列的Z分数
    z_scores = np.abs(stats.zscore(train_dataSet[column]))

    # 找出异常值（假设Z分数大于2为异常值）
    outliers = (z_scores > 2)

    # 计算异常值的比例
    outlier_ratio = outliers.mean()

    # 存储异常值比例
    outlier_ratios[column] = outlier_ratio
print("*"*30)
# 打印结果
print("异常值的比例:")
for column, ratio in outlier_ratios.items():
    print(f"{column}: {ratio:.2%}")



# 划分训练集中X_Train和y_Train
X_train = train_dataSet[noise_columns]
y_train = train_dataSet[columns]

# 划分测试集中X_test和y_test
X_test = test_dataSet[noise_columns]
y_test = test_dataSet[columns]

start_time = time.time() # Start timing here

print("-" * 30)
print("正在训练 MLPRegressor (深度神经网络) 模型...")

from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline

# 使用 MLPRegressor (深度神经网络)
# 针对环境数据复杂的非线性关系，神经网络通常能提供更好的拟合能力。
# 标准化 (StandardScaler) 被集成在 Pipeline 中，因为神经网络对数据尺度敏感。
mlp_params = {
    'hidden_layer_sizes': (128, 64),  # 两个隐藏层，分别有128和64个神经元
    'activation': 'relu',             # 激活函数
    'solver': 'adam',                 # 优化器
    'alpha': 0.0001,                  # L2正则化项
    'batch_size': 'auto',
    'learning_rate': 'adaptive',      # 学习率调整
    'learning_rate_init': 0.001,
    'max_iter': 2000,                 # 最大迭代次数
    'early_stopping': True,           # 早停策略防止过拟合
    'n_iter_no_change': 20,  
    'validation_fraction': 0.1,
    'random_state': 42,
    'verbose': True
}

# 管道：先标准化，再训练模型
# 注意：MLPRegressor 默认支持多输出，但在某些 sklearn 版本或特定设置下可能需要 MultiOutputRegressor 包装。
# 不过 sklearn 的 MLPRegressor 本身就支持多目标回归 (Multi-output regression)，所以直接使用即可。
# 如果为了和之前代码结构完全一致，保留 Pipeline 也可以直接 fit。
model = Pipeline([
    ('scaler', StandardScaler()),
    ('mlp', MLPRegressor(**mlp_params))
])

# 模型训练
model.fit(X_train, y_train)

# 预测值
y_predict = model.predict(X_test)


# 计算整体评估指标
r2 = r2_score(y_test, y_predict)
mse = mean_squared_error(y_test, y_predict)
print(f"\n模型评估结果:")
print(f"R2 Score (决定系数): {r2:.6f} (越接近1越好)")
print(f"MSE (均方误差): {mse:.6f} (越小越好)")


results = []
# 遍历y_test和y_predict，并且计算误差
for True_Value, Predicted_Value in zip(y_test.values, y_predict):
    error = np.abs(True_Value - Predicted_Value)
    # 格式化True_Value和Predicted_Value为原始数据格式
    formatted_true_value = ' '.join(map(str, True_Value))
    formatted_predicted_value = ' '.join(map(str, Predicted_Value))
    formatted_error = ' '.join(map(str, error))  # 修改ERROR数据格式
    results.append([formatted_true_value, formatted_predicted_value, formatted_error])  # 保存结果


# 结果写入CSV文件当中
result_df = pd.DataFrame(results, columns=['True_Value', 'Predicted_Value', 'Error'])
result_df.to_csv("result_MLP1.csv", index=False)
print(f"\n结果已保存至: result_MLP1.csv")

print("<*>"*50)

# 从CSV文件读取数据验证
data_check = pd.read_csv("result_MLP1.csv")

# 提取第三列数据 (Error)
column3 = data_check.iloc[:, 2]

# 将每行的多个数字拆分并转换为数字列表
numbers = column3.str.split(' ', expand=True).apply(pd.to_numeric)

# 计算平均误差
means = numbers.mean()

# 打印结果
print("各项指标平均误差为：\n", means)
print("总体平均误差:", means.mean())

end_time = time.time()

print(f"总耗时：{end_time - start_time : .3f}秒")
