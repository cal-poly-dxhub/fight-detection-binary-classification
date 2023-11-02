from manifest_definition import entries
import random



def main():
    valid_entries = list(filter(lambda entry: 'class-name' in entry['st-vrain-labeling4-clone-metadata'].keys(), entries))
    positive_entries = list(filter(lambda entry: entry['st-vrain-labeling4-clone-metadata']['class-name'] == "Fight",
                                   valid_entries))

    negative_entries = list(filter(lambda entry: entry['st-vrain-labeling4-clone-metadata']['class-name'] == "No Fight",
                                   valid_entries))

    target_num_neg_entries = ((len(positive_entries) * 100) / 20) - len(positive_entries)

    while len(negative_entries) > target_num_neg_entries:
        negative_entries.pop(random.randint(0, len(negative_entries) - 1))

    for entry in positive_entries:
        print(entry)

    for entry in negative_entries:
        print(entry)


main()



