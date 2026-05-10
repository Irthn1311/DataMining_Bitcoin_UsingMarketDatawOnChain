import json

filepath = '/home/nii/Documents/[code]sgu-2026-datamining-btc-onchain/mining/mining_dataset2_btc_onchain_daily.ipynb'

with open(filepath, 'r', encoding='utf-8') as f:
    nb = json.load(f)

new_source = [
    "from sklearn.metrics import precision_recall_fscore_support\n",
    "from IPython.display import display\n",
    "\n",
    "models = {\n",
    "    \"XGBoost\": XGBClassifier(n_estimators=N_ESTIMATORS, learning_rate=LEARNING_RATE, random_state=RANDOM_STATE),\n",
    "    \"Random Forest\": RandomForestClassifier(n_estimators=N_ESTIMATORS, random_state=RANDOM_STATE),\n",
    "    \"Logistic Regression\": LogisticRegression(max_iter=1000),\n",
    "}\n",
    "\n",
    "metrics_list = []\n",
    "\n",
    "for name, model in models.items():\n",
    "    model.fit(X_train, y_train)\n",
    "    y_pred = model.predict(X_test)\n",
    "    \n",
    "    acc = accuracy_score(y_test, y_pred)\n",
    "    precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average='macro')\n",
    "    \n",
    "    metrics_list.append({\n",
    "        \"Model\": name,\n",
    "        \"Accuracy\": acc,\n",
    "        \"Precision (Macro)\": precision,\n",
    "        \"Recall (Macro)\": recall,\n",
    "        \"F1-Score (Macro)\": f1\n",
    "    })\n",
    "    \n",
    "    print(f\"--- {name} ---\")\n",
    "    print(f\"Accuracy: {acc*100:.2f}%\")\n",
    "    print(classification_report(y_test, y_pred))\n",
    "    print(\"\\n\")\n",
    "\n",
    "# Tạo bảng so sánh\n",
    "comparison_df = pd.DataFrame(metrics_list)\n",
    "comparison_df.set_index(\"Model\", inplace=True)\n",
    "comparison_df = comparison_df.sort_values(by=\"Accuracy\", ascending=False)\n",
    "\n",
    "print(\"BẢNG SO SÁNH KẾT QUẢ CÁC MÔ HÌNH:\")\n",
    "display(comparison_df.style.format(\"{:.4f}\").background_gradient(cmap='Greens'))\n"
]

changed = False
for cell in nb.get('cells', []):
    if cell.get('cell_type') == 'code':
        source = cell.get('source', [])
        # Find the cell that defines 'models = {' and 'results = {}'
        if any("models = {" in line for line in source) and any("results = {}" in line for line in source):
            cell['source'] = new_source
            changed = True
            break

if changed:
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)
        f.write('\n')
    print("Notebook updated successfully.")
else:
    print("Could not find the target cell to update.")
