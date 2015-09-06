import csv
import mail

def does_it_all(inputData):
    """
    input file -> final dictionary
    """
    final_dictionary = {}
    collectiveScheduleDict = dictionary_from_textFile(inputData)
    for dates in collectiveScheduleDict:
        masterDictForDates = create_master_dict(dates)
        eventLists = collectiveScheduleDict[dates]
        busyList = generate_busy_blocks(eventLists)
        freeList = busy_to_free(busyList)
        update_dictionary(freeList, masterDictForDates)
        freeBlocksList = return_free_times(masterDictForDates)
        freeBlocksList.sort()
        final_dictionary[dates] = aggregate_free_blocks(freeBlocksList)
    return final_dictionary

def dictionary_from_textFile(database):
    """parse date and time from the given database"""
    f = open(database)
    dateAndTime={}
    for line in f:
        line = line.rstrip().lstrip()
        date = line[0:10]
        startTime = string_to_float(line[11:16])
        endTime = string_to_float(line[37:42])
        if date not in dateAndTime:
            dateAndTime[date]=[[startTime, endTime]]
        else:
            dateAndTime[date].append([startTime, endTime])
    f.close()
    return dateAndTime

def create_master_dict(date):
    """
    Generates master time table dict with "None" values
    """
    timeBlocksList = []
    timeBlock = 0

    for i in range(0,96):
        timeBlocksList.append(timeBlock)
        timeBlock += 0.25

    dateDict = {}
    dateDict[date] = dict.fromkeys(timeBlocksList)

    return dateDict

def generate_busy_blocks(eventsList):
    """
    From an event list with start times and end times, returns a list with busy blocks
    """
    busyList = []
    
    for eventTuple in eventsList:
        n = (eventTuple[1] - eventTuple[0]) / 0.25
        start = eventTuple[0]
        for i in range(0,int(n)):
            busyList.append(start)
            start += 0.25
    return busyList

def busy_to_free(list_of_busy_blocks):
    """
    get a list of one's busy blocks and spit out a list of his/her free times
    """
    list_of_all_blocks = [x / 4.0 for x in range(0, 96)]
    return [block for block in list_of_all_blocks if block not in list_of_busy_blocks]


def update_dictionary(list_of_free_blocks, masterDictionary):
    """
    use the generated list of free blocks to update the dictionary of 24-hr blocks
    """
    for block in list_of_free_blocks:
        masterDictionary[block] = 1

def return_free_times(masterDictionary):
    """
    Looks for keys that have the value None and adds that key to a list"
    """
    freeBlocksList = []
    
    for key in masterDictionary:
        if masterDictionary[key] == 1:
            freeBlocksList.append(key)
    return freeBlocksList

def string_to_float(timeString):
    """convert the time string to float"""
    minute = str(float(timeString[-2:])/60)
    return float(timeString[:2]+minute[1:])

def float_to_string(timeFloat):
     """convert the time float to string"""
     time = str(timeFloat)
     minute_in_string = str(int(float(time[time.index('.'):])*60))
     if minute_in_string == "0":
         minute_in_string += "0"
     hour_in_string = time[0:time.index('.')]
     time_in_string = hour_in_string + ':' + minute_in_string
     return time_in_string

def aggregate_free_blocks(lst_of_floats):
    string_message = 'these periods are free for coordination: ' + float_to_string(lst_of_floats[0])
    for i in range (1, len(lst_of_floats)):
        if lst_of_floats[i] - lst_of_floats[i-1] > 0.25:
            string_message+=' to ' + float_to_string(lst_of_floats[i-1] + 0.25) + ', ' + float_to_string(lst_of_floats[i])
    string_message+= ' to ' + float_to_string(lst_of_floats[-1]+0.25)
    return string_message

def send_mail(contentOfMail):

    mail.gmail_user = "penncoordinatorapp"
    mail.gmail_pwd = "upennmcit"
    subject = "Coordinate: These are the best times!"
    content = contentOfMail

    f = open("email_addresses.txt", "r")

    for address in f:
        address = address.replace("\n","")   
        mail.mail(address, subject, content)       

    f.close()
    

def main():
    """
    It's the main
    """

    ryan = does_it_all('times.txt')
    keysAsList = ryan.keys()
    keysAsList.sort()

    emailContent = ""

    for i in keysAsList:
        emailContent += 'On' + " " + i + " " + ryan[i] + "\n"

    send_mail(emailContent)
    

if __name__ == '__main__':
    main()
