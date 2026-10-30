import pandas as pd

df = pd.read_csv('C:/Users/Arsh/Documents/aiAgents/phase1/data/data.csv', encoding='ISO-8859-1')
print(df.shape)
print(df.head())
print(df.tail())
print(df.info())
print(df.isnull().sum())