import matplotlib.pyplot as pp
import numpy as np
import pandas as pd

from collections import OrderedDict
from sklearn.metrics import confusion_matrix
from sklearn.metrics import precision_recall_curve, roc_auc_score, roc_curve
from sklearn.model_selection import train_test_split as split


DTYPE = 'uint8'
NEGATIVE = 0
POSITIVE = 1


class Dataset:
    def __init__(self, data,
                 test_size=0.3,
                 weight=False,
                 negative=NEGATIVE,
                 positive=POSITIVE,
                 oversample=False,
                 undersample=False):
        data_train, data_test = split(data, test_size=test_size, random_state=0)
        if oversample: data_train = Dataset.oversample(data_train, 'Income')
        if undersample: data_train = Dataset.undersample(data_train, 'Income')
        if weight:
            positive_size = (data_train['Income'] == positive).sum()
            negative_size = data_train.shape[0] - positive_size
            ratio = negative_size / positive_size
            data_train = Dataset.weight(data_train, 'Income',
                                        {negative: 1.0, positive: ratio})
            data_test = Dataset.weight(data_test, 'Income',
                                       {negative: 1.0, positive: 1.0})
        self.y_train = data_train.pop('Income')
        self.x_train = data_train
        self.y_test = data_test.pop('Income')
        self.x_test = data_test

    def oversample(data, column, negative=NEGATIVE, positive=POSITIVE):
        data_negative = data[data[column] == negative]
        data_positive = data.loc[np.random.choice(
            data[data[column] == positive].index,
            len(data_negative), replace=True)]
        data = pd.concat([data_positive, data_negative])
        return data.sample(frac=1).reset_index(drop=True)

    def undersample(data, column, negative=NEGATIVE, positive=POSITIVE):
        data_positive = data[data[column] == positive]
        data_negative = data.loc[np.random.choice(
            data[data[column] == negative].index,
            len(data_positive), replace=False)]
        data = pd.concat([data_positive, data_negative])
        return data.sample(frac=1).reset_index(drop=True)

    def weight(data, column, weight):
        data['Weight'] = data[column].map(weight)
        return data


def column_defaults(categorical_names=[]):
    defaults = []
    categorical_names += column_variants().keys()
    for name in column_names():
        defaults.append((name, ['' if name in categorical_names else 0]))
    return OrderedDict(defaults)


def column_names():
    return [
        'Age',
        'WorkClass',
        'FinalSamplingWeight',
        'Education',
        'EducationNumber',
        'MaritalStatus',
        'Occupation',
        'Relationship',
        'Race',
        'Sex',
        'CapitalGain',
        'CapitalLoss',
        'HoursPerWeek',
        'NativeCountry',
        'Income',
    ]


def column_variants():
    return {
        'Education': [
            '10th',
            '11th',
            '12th',
            '1st-4th',
            '5th-6th',
            '7th-8th',
            '9th',
            'Assoc-acdm',
            'Assoc-voc',
            'Bachelors',
            'Doctorate',
            'HS-grad',
            'Masters',
            'Preschool',
            'Prof-school',
            'Some-college',
        ],
        'MaritalStatus': [
            'Divorced',
            'Married-AF-spouse',
            'Married-civ-spouse',
            'Married-spouse-absent',
            'Never-married',
            'Separated',
            'Widowed',
        ],
        'NativeCountry': [
            'Cambodia',
            'Canada',
            'China',
            'Columbia',
            'Cuba',
            'Dominican-Republic',
            'Ecuador',
            'El-Salvador',
            'England',
            'France',
            'Germany',
            'Greece',
            'Guatemala',
            'Haiti',
            'Holand-Netherlands',
            'Honduras',
            'Hong',
            'Hungary',
            'India',
            'Iran',
            'Ireland',
            'Italy',
            'Jamaica',
            'Japan',
            'Laos',
            'Mexico',
            'Nicaragua',
            'Outlying-US(Guam-USVI-etc)',
            'Peru',
            'Philippines',
            'Poland',
            'Portugal',
            'Puerto-Rico',
            'Scotland',
            'South',
            'Taiwan',
            'Thailand',
            'Trinadad&Tobago',
            'United-States',
            'Vietnam',
            'Yugoslavia',
        ],
        'Occupation': [
            'Adm-clerical',
            'Armed-Forces',
            'Craft-repair',
            'Exec-managerial',
            'Farming-fishing',
            'Handlers-cleaners',
            'Machine-op-inspct',
            'Other-service',
            'Priv-house-serv',
            'Prof-specialty',
            'Protective-serv',
            'Sales',
            'Tech-support',
            'Transport-moving',
        ],
        'Relationship': [
            'Husband',
            'Not-in-family',
            'Other-relative',
            'Own-child',
            'Unmarried',
            'Wife',
        ],
        'Race': [
            'Amer-Indian-Eskimo',
            'Asian-Pac-Islander',
            'Black',
            'Other',
            'White',
        ],
        'Sex': [
            'Female',
            'Male',
        ],
        'WorkClass': [
            'Federal-gov',
            'Local-gov',
            'Never-worked',
            'Private',
            'Self-emp-inc',
            'Self-emp-not-inc',
            'State-gov',
            'Without-pay',
        ],
    }


def compute_confusion(y_true, y_predicted, y_score, beta=1):
    matrix = confusion_matrix(y_true, y_predicted)
    tn, tp = matrix[0, 0], matrix[1, 1]
    fn, fp = matrix[1, 0], matrix[0, 1]
    return OrderedDict([
        ('Accuracy', (tp + tn) / (tp + fn + tn + fp)),
        ('Precision', tp / (tp + fp)),
        ('Sensitivity', tp / (tp + fn)),
        ('Specificity', tn / (tn + fp)),
        ('F{} score'.format(beta), ((1 + beta**2) * tp) /
                                   ((1 + beta**2) * tp + beta**2 * fn + fp)),
        ('ROC-AUC', roc_auc_score(y_true, y_score)),
    ])


def encode_categorical(data, column, drop=None, keep=None):
    dummies = pd.get_dummies(data[column], drop_first=True)
    if keep: drop = list(set(dummies.columns) - set(keep))
    if drop: dummies.drop(drop, axis=1, inplace=True)
    dummies.columns = ['{}[{}]'.format(column, variant)
                       for variant in dummies.columns]
    data = data.join(dummies)
    data.drop([column], axis=1, inplace=True)
    return data


def load_data(path, negative=NEGATIVE, positive=POSITIVE,
              dtype=DTYPE, **arguments):
    data = pd.read_csv(path, names=column_names(), sep=r'\s*,\s*',
                       engine='python', na_values='?', index_col=False,
                       **arguments)
    mapping = {'<=50K.': negative, '<=50K': negative,
               '>50K.': positive, '>50K': positive}
    data['Income'] = data['Income'].map(mapping).astype(dtype)
    return data


def plot_confusion(y_true, y_predicted, y_score):
    _, axes = pp.subplots(1, 3, figsize=(15, 4))
    pp.sca(axes[0])
    plot_confusion_matrix(y_true, y_predicted)
    pp.sca(axes[1])
    plot_roc(y_true, y_score)
    pp.sca(axes[2])
    plot_precision_recall(y_true, y_score)


def plot_confusion_matrix(y_true, y_predicted):
    matrix = confusion_matrix(y_true, y_predicted)
    matrix = matrix / matrix.sum(axis=1)[:, None]
    count = matrix.shape[0]
    pp.imshow(matrix, cmap='Blues')
    pp.xticks(np.arange(count), ['Negative', 'Positive'])
    pp.yticks(np.arange(count), ['Negative', 'Positive'])
    middle = matrix.max() / 2.0
    for i in range(count):
        for j in range(count):
            color = 'white' if matrix[i, j] > middle else 'black'
            pp.text(j, i, '{:.2f}%'.format(100 * matrix[i, j]),
                    horizontalalignment='center', color=color)
    pp.ylabel('True')
    pp.xlabel('Predicted')


def plot_precision_recall(y_true, y_score, t_star=0.5):
    base = (y_true == 1).sum() / len(y_true)
    y, x, t = precision_recall_curve(y_true, y_score)
    i = np.argmin(np.abs(t - t_star))
    pp.step(x, y, where='post')
    pp.plot([0, 1], [base, base], linestyle='--')
    pp.plot(x[i], y[i], marker='o', markersize=10)
    pp.xlabel('Recall')
    pp.ylabel('Precision')
    pp.ylim([0.0, 1.0])
    pp.xlim([0.0, 1.0])


def plot_roc(y_true, y_score, t_star=0.5):
    x, y, t = roc_curve(y_true, y_score)
    i = np.argmin(np.abs(t - t_star))
    pp.step(x, y, where='post')
    pp.plot([0, 1], [0, 1], linestyle='--')
    pp.plot(x[i], y[i], marker='o', markersize=10)
    pp.xlabel('False positive rate')
    pp.ylabel('True positive rate')
    pp.ylim([0.0, 1.0])
    pp.xlim([0.0, 1.0])
