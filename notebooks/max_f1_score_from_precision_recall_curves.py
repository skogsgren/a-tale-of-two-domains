# this script simply reads the tex file output by the tikzplotlib
# library and outputs the top10 precision/recall value pairs with the
# largest f1_values.

nTuples = list()
with open("precision_recall_curve.tex", "r") as f:
    for line in [x for x in f]:
        try:
            if (float(line[0]) >= 0 and float(line[0]) <= 1):
                nTuples.append(
                    tuple([float(x) for x in line.strip().split(" ")])
                )
        except ValueError:
            pass

nF1 = list()
for t in nTuples:
    precision, recall = t[0], t[1]
    f1_score = 2 * (precision * recall) / (precision + recall)
    nF1.append((f1_score, precision, recall))

topTen = list(sorted(nF1, key=lambda x: x[0], reverse=True))[:10]
print(topTen)