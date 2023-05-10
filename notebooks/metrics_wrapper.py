from sklearn.metrics import confusion_matrix 
from sklearn.metrics import f1_score
from sklearn.metrics import precision_score
from sklearn.metrics import recall_score
from transformers import pipeline
from datasets import Dataset
import seaborn as sns
import matplotlib.pyplot as plt


class MetricsWrapper():
    def __init__(self, model_pipeline: pipeline, data: Dataset):
        self.tokenizer_kwargs = {'padding':True, 'truncation':True, 'max_length':512}
        self.model_pipeline = model_pipeline
        self.data = data
        self.metrics = self.get_metrics()

    def get_metrics(self) -> dict:
        """ Calculates f1_score and confusion matrix, displays them, and returns them"""
        predictions = self.model_pipeline(self.data["text"], **self.tokenizer_kwargs)
        y_pred = [1 if x["label"] == "LABEL_1" else 0 for x in predictions]
        y_true = self.data["label"]
        confidence = [x["score"] for x in predictions]
        f1 = f"{f1_score(y_true, y_pred):.2f}"
        precision = f"{precision_score(y_true, y_pred):.2f}"
        recall = f"{recall_score(y_true, y_pred):.2f}"
        conf_matrix = confusion_matrix(y_pred=y_pred, y_true=y_true)
        predictions = list(zip(self.data["text"], y_true, y_pred, confidence))
        return {"f1_score": f1, "precision": precision, "recall": recall, "conf_matrix": conf_matrix, "predictions": predictions}
    
    def display_metrics(self):
        print(f"precision: {self.metrics['precision']}")
        print(f"recall: {self.metrics['recall']}")
        print(f"f1_score: {self.metrics['f1_score']}")
        ax= plt.subplot()
        sns.heatmap(self.metrics["conf_matrix"], annot=True, fmt='g', ax=ax);
        ax.set_xlabel('Predicted labels');ax.set_ylabel('True labels'); 
        ax.set_title('Confusion Matrix'); 
        ax.xaxis.set_ticklabels(['0', '1']); ax.yaxis.set_ticklabels(['0', '1']);
        
        
class ChatGPTMetricsWrapper:
    def __init__(self, *args):
        self.metrics = {
            "f1_score": args[0],
            "precision": args[1],
            "recall": args[2],
            "conf_matrix": args[3],
            "predictions": args[4]
        }
    def display_metrics(self):
        print(f"precision: {self.metrics['precision']:.2f}")
        print(f"recall: {self.metrics['recall']:.2f}")
        print(f"f1_score: {self.metrics['f1_score']:.2f}")
        ax= plt.subplot()
        sns.heatmap(self.metrics["conf_matrix"], annot=True, fmt='g', ax=ax);
        ax.set_xlabel('Predicted labels');ax.set_ylabel('True labels'); 
        ax.set_title('Confusion Matrix'); 
        ax.xaxis.set_ticklabels(['0', '1']); ax.yaxis.set_ticklabels(['0', '1']);


class ThreeWayConfMatrix:
    def __init__(self, y_pred1, y_pred2, y_true, title="Three-way Confusion Matrix"):
        self.title = title
        self.cm3 = [
            [0, 0, 0, 0],
            [0, 0, 0, 0]
        ]
        # to store indices so that the text can be accessed later
        self.idx_list = [
            [[], [], [], []],
            [[], [], [], []]
        ]
        for idx, x in enumerate(zip(y_pred1, y_pred2, y_true)):
            y1, y2, y_true = x[0], x[1], x[2]  # to make it easier to read
            if y_true == 0:
                if y1 == 0 and y2 == 0:
                    self.cm3[0][0] += 1
                    self.idx_list[0][0].append(idx)
                elif y1 == 1 and y2 == 0:
                    self.cm3[0][1] += 1
                    self.idx_list[0][1].append(idx)
                elif y1 == 0 and y2 == 1:
                    self.cm3[0][2] += 1
                    self.idx_list[0][2].append(idx)
                elif y1 == 1 and y2 == 1:
                    self.cm3[0][3] += 1
                    self.idx_list[0][3].append(idx)
            elif y_true == 1:
                if y1 == 0 and y2 == 0:
                    self.cm3[1][0] += 1
                    self.idx_list[1][0].append(idx)
                elif y1 == 1 and y2 == 0:
                    self.cm3[1][1] += 1
                    self.idx_list[1][1].append(idx)
                elif y1 == 0 and y2 == 1:
                    self.cm3[1][2] += 1
                    self.idx_list[1][2].append(idx)
                elif y1 == 1 and y2 == 1:
                    self.cm3[1][3] += 1
                    self.idx_list[1][3].append(idx)

    def display(self):
        ax= plt.subplot()
        sns.heatmap(self.cm3, annot=True, fmt='g', ax=ax);
        ax.set_xlabel('Predicted labels');ax.set_ylabel('True labels'); 
        ax.set_title(self.title); 
        ax.xaxis.set_ticklabels(['0/0', '1/0', '0/1', '1/1']); ax.yaxis.set_ticklabels(['0', '1']);
        
    def save_cm_to_disk(self, path: str):
        ax= plt.subplot()
        sns.heatmap(self.cm3, annot=True, fmt='g', ax=ax);
        ax.set_xlabel('Predicted labels');ax.set_ylabel('True labels'); 
        ax.set_title(self.title); 
        ax.xaxis.set_ticklabels(['0/0', '1/0', '0/1', '1/1']); ax.yaxis.set_ticklabels(['0', '1']);
        plt.savefig(path, dpi=1600)
        print(f"Successfully saved plot to {path}")