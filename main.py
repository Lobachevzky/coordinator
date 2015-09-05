def create_master_dict():
    """
    Generates master time table dict with "None" values
    """
    timeBlocksList = []
    timeBlock = 0

    for i in range(0,48):
        timeBlocksList.append(timeBlock)
        timeBlock += 0.5

    return dict.fromkeys(timeBlocksList)

def generate_busy_blocks(eventsList):
    """
    From an event list with start times and end times, returns a list with busy blocks

    """
    busyList = []
    
    for eventTuple in eventsList:
        n = (eventTuple[1] - eventTuple[0]) / 0.5
        start = eventTuple[0]
        for i in range(0,int(n)):
            busyList.append(start)
            start += 0.5
    return busyList

def busy_to_free (list_of_busy_blocks):
    """
    get a list of one's busy blocks and spit out a list of his/her free times
    """
    list_of_all_blocks = [x / 2.0 for x in range(0, 48)]
    return [block for block in list_of_all_blocks if block not in list_of_busy_blocks]


def update_dictionary(list_of_free_blocks, masterDictionary):
    """
    use the generated list of free blocks to update the dictionary of 24-hr blocks
    """
##    listOf24Hrs = [x / 2.0 for x in range(0, 48)]
##    dictionaryOf24Hrs = dict.fromkeys(listOf24Hrs)
    for block in list_of_free_blocks:
        masterDictionary[block] = 1

eventsList = [[1.5, 4], [2.5, 3.5]]

def main():
    """
    It's the main
    """
    
    masterDict = create_master_dict()
    update_dictionary(busy_to_free(generate_busy_blocks(eventsList)), masterDict)
    print "New Dictionary : %s" %  str(masterDict)
    

if __name__ == '__main__':
    main()
