import json
import itertools
import pprint
import urllib.request

def to_milliseconds(string):
    """This function takes a time string of the form hr:min:sec.millisec and returns an integer 
    number of milliseconds."""
    hr,min,secms = string.split(":")
    sec,milli = secms.split(".")
    return int(hr)*3600*1000+int(min)*60*1000+int(sec)*1000+int(milli)

def load_json_from_api(url):
    """Takes a url and loads the json data as a python dict"""
    response = urllib.request.urlopen(url)
    data = json.loads(response.read())
    return data

def extract_result_table(json, up_until=None):
    results = {}
    for element in json['race_results']:
        time = to_milliseconds(element['results_time'])
        interval = element['results_interval_name']
        identifier = element['results_entry_id']
        if identifier not in results:
            results[identifier] = {}
        if up_until is None or time < up_until:
            results[identifier][interval] = time
    return results

def create_leader_board(results_table):
    """Creates a list of identifiers in order

    Args:
        results_table (dict): The output of extract_results_table

    Returns:
        list: An ordered list of identifiers
    """
    # Generate a list of markers in order from first to last
    markers = []
    for identifier in results_table:
        new_markers = sorted(list(results_table[identifier].keys()), key=lambda i:results_table[identifier].get(i))
        for i, checkpoint in enumerate(new_markers):
            if checkpoint not in markers:
                if i==0:
                    markers = [checkpoint] + markers
                else:
                    insert_at = markers.index(new_markers[i-1])
                    markers = markers[:insert_at] + [checkpoint] + markers[insert_at:]
            else:
                continue
    
    # Use the most recent 
    leaderboard = []
    for checkpoint in markers: # Step through the checkpoint
        times = [(results_table[identifier][checkpoint],identifier) for identifier in results_table if checkpoint in results_table[identifier] ]
        times.sort() # Generate a table of the format [(time,identifier),...] for this checkpoint
        for time, identifier in times: #Step through this list in order
            if identifier not in leaderboard: # If we haven't seen this identifier yet
                leaderboard.append(identifier) # Add it to the leaderboard

    return leaderboard

def get_leaderboard(json_string):
    """A lifting function to go straight from the raw json string to a leaderboard"""
    data = json.loads(json_string)
    results_table = extract_result_table(data)
    leaderboard = create_leader_board(results_table)
    return leaderboard

def parse_for_ids(json):
    """Parse the json dict for racer identifiers"""
    ids = {}
    for item in json['race_results']:
        identifier = item['results_entry_id']
        if identifier in ids:
            continue
        first = item['results_first_name']
        last = item['results_last_name']
        bib = item['results_bib']
        state = item['results_state_code']
        country = item['results_country_code']
        ids[identifier] = {'first_name':first, 'last_name':last, 'bib':bib,
                           'state':state, 'country':country}
    return ids

def parse_for_checkpoints(json):
    """Parse the json dict for checkpoint times"""
    cps = {}
    for item in json['race_results']:
        identifier = item['results_entry_id']
        if identifier not in cps:
            cps[identifier] = {}
        interval_name = item['results_interval_name']
        cps[identifier][interval_name] = item['results_time']
    return cps

def render_leaderboard_as_json(json):
    """Take all of the above and produce a json dictionary of a leaderboard"""
    ids = parse_for_ids(json)
    checkpoints = parse_for_checkpoints(json)
    results_table = extract_result_table(json)
    leader_board = create_leader_board(results_table)
    output = {}
    for place, identifier in enumerate(leader_board):
        output[identifier] = {}
        output[identifier]['place'] = place + 1
        output[identifier].update(ids[identifier])
        output[identifier].update(checkpoints[identifier])
    return output
    
def test(json_data, milliseconds_step=60000):
    results = extract_result_table(json_data)

    # How long do we run for?
    runfor = 0
    for identifier in results:
        for checkpoint in results[identifier]:
            if runfor < results[identifier][checkpoint]:
                runfor = results[identifier][checkpoint]
    
    for time in range(0,runfor,milliseconds_step):
        print(time, create_leader_board(extract_result_table(json_data, time)))




if __name__ == "__main__":
    # with open('output.json','r') as f:
    #     jsonstr = f.read()
    # data = json.loads(jsonstr)
    # print(get_leaderboard(jsonstr))
    # print(list(data.keys()))
    data = load_json_from_api("https://api.chronotrack.com/api/race/127700/results?format=json&client_id=727dae7f&user_id=nwiegand%40chronotrack.com&user_pass=676a10864eb8cc0e1cab1abc71b6b5bc775d0a8a&page=1&size=50&interval=all&mode=ctlive#race_results/0")
    print(json.dumps(render_leaderboard_as_json(data)))