import json
import timeit


with open('data/transactions.json', 'r') as file:
    transactions = json.load(file)

#Linear search
def linear_search(transactions, target):
    for transaction in transactions:
        if transaction["id"] == target:
            return transaction
    return None

#Turn the transactions into a dictionary
transactions_dict = {}
for transaction in transactions:
    transactions_dict[transaction["id"]] = transaction

#Dictionary_search
def dictionary_search(transactions_dict, target):
    return transactions_dict.get(target)  

#Test time taken by each search 
targets = [transaction["id"] for transaction in transactions]
results = []
number_of_runs = 1000
for target in targets:
    linear_time = timeit.timeit(
        lambda: linear_search(transactions, target),
        number=number_of_runs
    )
    dictionary_time = timeit.timeit(
        lambda: dictionary_search(transactions_dict, target),
        number=number_of_runs
    )

    result = {
        "records": len(transactions),
        "transaction_id" : target,
        "number_of_runs" : number_of_runs,
        "linear_time": linear_time,
        "dictionary_time": dictionary_time
    }
    results.append(result)

#save the results in a json
with open("data/search_results.json", "w") as file:
    json.dump(results, file, indent=4)

print("running...")
print("search results saved successfully in search_results.json")