# First do a recursice search of the labeled data bucket
# aws s3 ls s3://bucketname/ --recursive > labeled_files.txt
# grab just the key portion of the file name
# awk '{print $4}' labeled_files.txt  > s3-labeled_files.txt
# Open the file for reading
FILE_NAME = "s3-labeled_files.txt"
group_indexer = 0
with open(FILE_NAME, "r") as file:

    # Create a list of groups for indexing i.e. train, val, test
    group = []
    output = []
    identifier = {'NoFight': 0, 'Fight': 1}
    # line looks like
    # val/NoFight/Fight_9---000_frame_480.jpg
 
    for line in file:
        # parse key to determine which group
        index = line.find('/')
        if index != -1:
            # check the group
            group_name = line[:index]
            # We've seen this group before
            if group_name in group:
                # determine the identifier
                second_index = line.find('/', index + 1)
                indentifier_str = line[index+1:second_index]
                #print (indentifier_str)
                # Find identifier code for this image
                print (group_indexer, "\t", identifier.get(indentifier_str), line)
                output.append(f"{group_indexer}\t{identifier.get(indentifier_str)}\t{line}")
                group_indexer = group_indexer + 1
            #create new group
            else:
                print("New group", group_name)
                group.append(group_name)
                #group_indexer = 0
         
        else:
            print("The line does not contain a '/' character.\n")

        # Print the line to the console
        #print(line.strip())

with open("sagemaker.lst", "w") as sagemaker_out:
    for line in output:
        # Write each line to the new file
        sagemaker_out.write(line)