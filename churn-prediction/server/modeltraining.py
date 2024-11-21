# code from goolge collab

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv("churn.csv")

df

df.describe()

sns.set_style(style="whitegrid")
plt.figure(figsize=(12,10))

sns.countplot(x="Exited", data=df)
plt.title("Distribution of Churn")

sns.histplot(data=df, x="Age", kde=True)
plt.title("Age Distribution")

sns.scatterplot(data=df, x="CreditScore", y="Age", hue="Exited")
plt.title("Credit Score vs Age")

sns.boxplot(x="Exited", y="Balance", data=df)
plt.title("Balance Distribution by Churn")

sns.boxplot(x="Exited", y="CreditScore", data=df)
plt.title("Credit Score Distribution by Churn")

features = df.drop('Exited', axis=1)

features

target = df['Exited']

features = features.drop(['RowNumber', 'CustomerId', 'Surname'], axis=1)

features = features.dropna() // feature selection - drop redundant features

features = pd.get_dummies(features, columns=["Geography", "Gender"])
// hot encoding - feature transformation

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)

scaler = StandardScaler() // standardization - feature transformation
X_train = scaler.fit_transform(X_train)
X_test = scaler.fit_transform(X_test)

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import pickle
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.ensemble import AdaBoostClassifier

lr_model = LogisticRegression(random_state=42)

lr_model.fit(X_train, y_train)

lr_predictions = lr_model.predict(X_test)

lr_accuracy= accuracy_score(y_test, lr_predictions)

lr_accuracy
0.811

def evaluate_and_save_model(model, X_train, X_test, y_train, y_test, filename):
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"{model.__class__.__name__} Accuracy: {accuracy:4f}")
    print(f"\nClassification Report: \n{classification_report(y_test, y_pred)}")
    print("---------------------------")

    with open(filename, "wb") as file:
        pickle.dump(model, file)

    print(f"Model saved as {filename}")

lr_model = LogisticRegression(random_state=42)
evaluate_and_save_model(lr_model, X_train, X_test, y_train, y_test, "lr_model.pkl")

xgb_model = xgb.XGBClassifier(random_state=42)
evaluate_and_save_model(xgb_model, X_train, X_test, y_train, y_test, "xgb_model.pkl")

dt_model = DecisionTreeClassifier(random_state=42)
evaluate_and_save_model(dt_model, X_train, X_test, y_train, y_test, "dt_model.pkl")

rf_model = RandomForestClassifier(random_state=42)
evaluate_and_save_model(rf_model, X_train, X_test, y_train, y_test, "rf_model.pkl")

nb_model = GaussianNB()
evaluate_and_save_model(nb_model, X_train, X_test, y_train, y_test, "nb_model.pkl")

knn_model = KNeighborsClassifier()
evaluate_and_save_model(knn_model, X_train, X_test, y_train, y_test, "knn_model.pkl")

svm_model = SVC(random_state=42)
evaluate_and_save_model(svm_model, X_train, X_test, y_train, y_test, "svm_model.pkl")

gb_model = GradientBoostingClassifier(random_state=42)
evaluate_and_save_model(gb_model, X_train, X_test, y_train, y_test, "gb_model.pkl")

et_model = ExtraTreesClassifier(random_state=42)
evaluate_and_save_model(et_model, X_train, X_test, y_train, y_test, "et_model.pkl")

ab_model = AdaBoostClassifier(random_state=42)
evaluate_and_save_model(ab_model, X_train, X_test, y_train, y_test, "ab_model.pkl")
---------------------------
LogisticRegression Accuracy: 0.811000

Classification Report:
              precision    recall  f1-score   support

           0       0.83      0.96      0.89      1607
           1       0.55      0.21      0.30       393

    accuracy                           0.81      2000
   macro avg       0.69      0.58      0.60      2000
weighted avg       0.78      0.81      0.77      2000

---------------------------
Model saved as lr_model.pkl
XGBClassifier Accuracy: 0.745500

Classification Report:
              precision    recall  f1-score   support

           0       0.88      0.80      0.83      1607
           1       0.39      0.54      0.45       393

    accuracy                           0.75      2000
   macro avg       0.63      0.67      0.64      2000
weighted avg       0.78      0.75      0.76      2000

---------------------------
Model saved as xgb_model.pkl
DecisionTreeClassifier Accuracy: 0.785000

Classification Report:
              precision    recall  f1-score   support

           0       0.88      0.85      0.86      1607
           1       0.46      0.51      0.48       393

    accuracy                           0.79      2000
   macro avg       0.67      0.68      0.67      2000
weighted avg       0.80      0.79      0.79      2000

---------------------------
Model saved as dt_model.pkl
RandomForestClassifier Accuracy: 0.864500

Classification Report:
              precision    recall  f1-score   support

           0       0.88      0.96      0.92      1607
           1       0.75      0.46      0.57       393

    accuracy                           0.86      2000
   macro avg       0.82      0.71      0.75      2000
weighted avg       0.85      0.86      0.85      2000

---------------------------
Model saved as rf_model.pkl
GaussianNB Accuracy: 0.818500

Classification Report:
              precision    recall  f1-score   support

           0       0.86      0.93      0.89      1607
           1       0.56      0.38      0.45       393

    accuracy                           0.82      2000
   macro avg       0.71      0.65      0.67      2000
weighted avg       0.80      0.82      0.80      2000

---------------------------
Model saved as nb_model.pkl
KNeighborsClassifier Accuracy: 0.824000

Classification Report:
              precision    recall  f1-score   support

           0       0.86      0.94      0.90      1607
           1       0.59      0.36      0.44       393

    accuracy                           0.82      2000
   macro avg       0.72      0.65      0.67      2000
weighted avg       0.80      0.82      0.81      2000

---------------------------
Model saved as knn_model.pkl
SVC Accuracy: 0.856000

Classification Report:
              precision    recall  f1-score   support

           0       0.86      0.97      0.92      1607
           1       0.77      0.38      0.51       393

    accuracy                           0.86      2000
   macro avg       0.82      0.68      0.71      2000
weighted avg       0.85      0.86      0.84      2000

---------------------------
Model saved as svm_model.pkl
GradientBoostingClassifier Accuracy: 0.864500

Classification Report:
              precision    recall  f1-score   support

           0       0.88      0.96      0.92      1607
           1       0.74      0.48      0.58       393

    accuracy                           0.86      2000
   macro avg       0.81      0.72      0.75      2000
weighted avg       0.85      0.86      0.85      2000

---------------------------
Model saved as gb_model.pkl
ExtraTreesClassifier Accuracy: 0.868500

Classification Report:
              precision    recall  f1-score   support

           0       0.88      0.97      0.92      1607
           1       0.78      0.46      0.58       393

    accuracy                           0.87      2000
   macro avg       0.83      0.71      0.75      2000
weighted avg       0.86      0.87      0.85      2000

---------------------------
Model saved as et_model.pkl
/usr/local/lib/python3.10/dist-packages/sklearn/ensemble/_weight_boosting.py:527: FutureWarning: The SAMME.R algorithm (the default) is deprecated and will be removed in 1.6. Use the SAMME algorithm to circumvent this warning.
  warnings.warn(
AdaBoostClassifier Accuracy: 0.853500

Classification Report:
              precision    recall  f1-score   support

           0       0.88      0.94      0.91      1607
           1       0.68      0.48      0.56       393

    accuracy                           0.85      2000
   macro avg       0.78      0.71      0.74      2000
weighted avg       0.84      0.85      0.84      2000

---------------------------
Model saved as ab_model.pkl


---------------------------
feature_importances = xgb_model.feature_importances_
feature_names = features.columns

feature_importances

feature_importances_df= pd.DataFrame({
    'feature': feature_names,
    'importance': feature_importances
})

feature_importances_df

feature_importances_df = feature_importances_df.sort_values('importance', ascending=False)

feature_importances_df

feature	importance
4	NumOfProducts	0.323888
6	IsActiveMember	0.164146
1	Age	0.109550
9	Geography_Germany	0.091373
3	Balance	0.052786
8	Geography_France	0.046463
11	Gender_Female	0.045283
10	Geography_Spain	0.036855
0	CreditScore	0.035005
7	EstimatedSalary	0.032655
5	HasCrCard	0.031940
2	Tenure	0.030054
12	Gender_Male	0.000000

plt.figure(figsize=(10,6))
plt.bar(feature_importances_df['feature'], feature_importances_df['importance'])
plt.xticks(rotation=90)
plt.xlabel("Features")
plt.ylabel("Importance")
plt.tight_layout()
plt.show()

----------------

FEATURE ENGINEERING - feature creation and bucketization

features['CSV'] = df['Balance']*df['EstimatedSalary']/100000

features['AgeGroup']= pd.cut(df['Age'], bins=[0,30,45,60,100], labels=["Young", "MiddleAge", "Senior", "Elderly"])

features['TenureAgeRatio'] = df['Tenure']/df['Age']

features=pd.get_dummies(features, drop_first=True)
// hot encoding and removing redundant columns - feature selection

X_train, X_test, y_train, y_test = train_test_split(features, target, test_size=0.2, random_state=42)

---

xgboost_model = xgb.XGBClassifier(random_state=42)
evaluate_and_save_model(xgboost_model, X_train, X_test, y_train, y_test, "xgbFE_model.pkl")

XGBClassifier Accuracy: 0.859000

Classification Report:
              precision    recall  f1-score   support

           0       0.89      0.94      0.91      1607
           1       0.69      0.51      0.59       393

    accuracy                           0.86      2000
   macro avg       0.79      0.73      0.75      2000
weighted avg       0.85      0.86      0.85      2000

---------------------------
Model saved as xgbFE_model.pkl

dtree_model = DecisionTreeClassifier(random_state=42)
evaluate_and_save_model(dtree_model, X_train, X_test, y_train, y_test, "dt_FEmodel.pkl")

DecisionTreeClassifier Accuracy: 0.780500

Classification Report:
              precision    recall  f1-score   support

           0       0.88      0.84      0.86      1607
           1       0.45      0.52      0.48       393

    accuracy                           0.78      2000
   macro avg       0.66      0.68      0.67      2000
weighted avg       0.79      0.78      0.79      2000

---------------------------
Model saved as dt_FEmodel.pkl

---------------
SMOTE

from imblearn.over_sampling import SMOTE
smote = SMOTE(random_state=42)
X_resampled, y_resampled = smote.fit_resample(X_train, y_train)
evaluate_and_save_model(xgboost_model, X_resampled, X_test, y_resampled, y_test, "xgboost-SMOTE.pkl")

XGBClassifier Accuracy: 0.854500

Classification Report:
              precision    recall  f1-score   support

           0       0.89      0.93      0.91      1607
           1       0.65      0.55      0.60       393

    accuracy                           0.85      2000
   macro avg       0.77      0.74      0.75      2000
weighted avg       0.85      0.85      0.85      2000

---------------------------
Model saved as xgboost-SMOTE.pkl

evaluate_and_save_model(dtree_model, X_resampled, X_test, y_resampled, y_test, "dtree-SMOTE.pkl")

DecisionTreeClassifier Accuracy: 0.780500

Classification Report:
              precision    recall  f1-score   support

           0       0.88      0.84      0.86      1607
           1       0.45      0.54      0.49       393

    accuracy                           0.78      2000
   macro avg       0.67      0.69      0.68      2000
weighted avg       0.80      0.78      0.79      2000

---------------------------
Model saved as dtree-SMOTE.pkl

----------
ENSEMBLE

from sklearn.ensemble import VotingClassifier

voting_clf = VotingClassifier(estimators=[('xgboost', xgb.XGBClassifier(random_state=42)), ('rf', RandomForestClassifier(random_state=42)), ('svm', SVC(random_state=42, probability=True))], voting='soft')

evaluate_and_save_model(voting_clf, X_resampled, X_test, y_resampled, y_test, 'voting_clf.pkl')

VotingClassifier Accuracy: 0.866500

Classification Report:
              precision    recall  f1-score   support

           0       0.89      0.95      0.92      1607
           1       0.71      0.54      0.61       393

    accuracy                           0.87      2000
   macro avg       0.80      0.74      0.77      2000
weighted avg       0.86      0.87      0.86      2000

---------------------------
Model saved as voting_clf.pkl


voting_clf = VotingClassifier(estimators=[('xgboost', xgb.XGBClassifier(random_state=42)), ('rf', RandomForestClassifier(random_state=42)), ('svm', SVC(random_state=42, probability=True))], voting='hard')

evaluate_and_save_model(voting_clf, X_resampled, X_test, y_resampled, y_test, 'voting_clf1_soft.pkl')


evaluate_and_save_model(voting_clf, X_resampled, X_test, y_resampled, y_test, 'voting_clf1_soft.pkl')
VotingClassifier Accuracy: 0.861500

Classification Report:
              precision    recall  f1-score   support

           0       0.90      0.94      0.92      1607
           1       0.68      0.55      0.61       393

    accuracy                           0.86      2000
   macro avg       0.79      0.75      0.76      2000
weighted avg       0.85      0.86      0.86      2000

---------------------------
Model saved as voting_clf1_soft.pkl

voting_clf = VotingClassifier(estimators=[('xgboost', xgb.XGBClassifier(random_state=42)), ('rf', RandomForestClassifier(random_state=42)), ('svm', SVC(random_state=42, probability=True))], voting='hard')

evaluate_and_save_model(voting_clf, X_resampled, X_test, y_resampled, y_test, 'voting_clf1_hard.pkl')

VotingClassifier Accuracy: 0.853000

Classification Report:
              precision    recall  f1-score   support

           0       0.90      0.92      0.91      1607
           1       0.63      0.59      0.61       393

    accuracy                           0.85      2000
   macro avg       0.77      0.75      0.76      2000
weighted avg       0.85      0.85      0.85      2000

---------------------------
Model saved as voting_clf1_hard.pkl

from sklearn.ensemble import StackingClassifier

stacking_clf = StackingClassifier(
    estimators=[
        ('xgboost', xgb.XGBClassifier(random_state=42)),
        ('rf', RandomForestClassifier(random_state=42)),
        ('svm', SVC(random_state=42, probability=True))
    ],
    final_estimator=LogisticRegression()
)
evaluate_and_save_model(stacking_clf, X_resampled, X_test, y_resampled, y_test, 'stacking_clf.pkl')

StackingClassifier Accuracy: 0.857000

Classification Report:
              precision    recall  f1-score   support

           0       0.90      0.92      0.91      1607
           1       0.65      0.58      0.61       393

    accuracy                           0.86      2000
   macro avg       0.78      0.75      0.76      2000
weighted avg       0.85      0.86      0.85      2000

---------------------------
Model saved as stacking_clf.pkl


from sklearn.ensemble import BaggingClassifier
bagging_xgb = BaggingClassifier(
    estimator=xgb.XGBClassifier(
        random_state=42,
        max_depth=3,
        n_estimators=100,  # Internal estimators within each XGBoost
        learning_rate=0.1,
        scale_pos_weight=len(y_resampled[y_resampled == 0]) / len(y_resampled[y_resampled == 1])  # Handle imbalance
    ),
    n_estimators=10,  # Number of bagging iterations
    max_samples=0.8,  # Use 80% of the data for each bootstrapped sample
    max_features=1.0,  # Use all features for training
    bootstrap=True,  # Enable bootstrapped sampling
    random_state=42
)
evaluate_and_save_model(bagging_xgb, X_resampled, X_test, y_resampled, y_test, 'bagging_xgb_model.pkl')
BaggingClassifier Accuracy: 0.857000

Classification Report:
              precision    recall  f1-score   support

           0       0.90      0.93      0.91      1607
           1       0.66      0.57      0.61       393

    accuracy                           0.86      2000
   macro avg       0.78      0.75      0.76      2000
weighted avg       0.85      0.86      0.85      2000

---------------------------
Model saved as bagging_xgb_model.pkl

stacking_clf2 = StackingClassifier(
    estimators=[
        ('bagging_xgb', bagging_xgb),
        ('rf', RandomForestClassifier(random_state=42, class_weight='balanced'))
    ],
    final_estimator=LogisticRegression(class_weight='balanced')
)

evaluate_and_save_model(stacking_clf2, X_resampled, X_test, y_resampled, y_test, 'stacking_with_bagging.pkl')

StackingClassifier Accuracy: 0.854500

Classification Report:
              precision    recall  f1-score   support

           0       0.90      0.92      0.91      1607
           1       0.64      0.60      0.62       393

    accuracy                           0.85      2000
   macro avg       0.77      0.76      0.76      2000
weighted avg       0.85      0.85      0.85      2000

---------------------------
Model saved as stacking_with_bagging.pkl


stacking_clf3 = StackingClassifier(
    estimators=[
        ('bagging_xgb', bagging_xgb),
        ('dt', DecisionTreeClassifier(random_state=42, class_weight='balanced'))
    ],
    final_estimator=LogisticRegression(class_weight='balanced')
)

evaluate_and_save_model(stacking_clf3, X_resampled, X_test, y_resampled, y_test, 'stacking_with_bagging2.pkl')

StackingClassifier Accuracy: 0.851500

Classification Report:
              precision    recall  f1-score   support

           0       0.91      0.91      0.91      1607
           1       0.62      0.62      0.62       393

    accuracy                           0.85      2000
   macro avg       0.76      0.77      0.77      2000
weighted avg       0.85      0.85      0.85      2000

---------------------------
Model saved as stacking_with_bagging2.pkl

gb_model = GradientBoostingClassifier(
    n_estimators=100,      # Number of trees
    learning_rate=0.1,     # Step size for each tree
    max_depth=3,           # Depth of each tree
    random_state=42
)

evaluate_and_save_model(gb_model, X_resampled, X_test, y_resampled, y_test, 'gbClassifier.pkl')

GradientBoostingClassifier Accuracy: 0.858000

Classification Report:
              precision    recall  f1-score   support

           0       0.90      0.93      0.91      1607
           1       0.66      0.56      0.61       393

    accuracy                           0.86      2000
   macro avg       0.78      0.75      0.76      2000
weighted avg       0.85      0.86      0.85      2000

---------------------------
Model saved as gbClassifier.pkl


