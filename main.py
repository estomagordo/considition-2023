import os
import json
from copy import deepcopy
from time import time
from scoring import calculateScore
from api import getGeneralData, getMapData, submit
from data_keys import (
    MapNames as MN,
    LocationKeys as LK,
    ScoringKeys as SK,
    HotspotKeys as HK,
    GeneralKeys as GK,
    CoordinateKeys as CK,
)

api_key = ''
game_folder = "my_games"
bestfile = 'best.txt'
max_locations = 2
max_requests = 5
max_requests_time = 11.0

def main():
    bestpermap = {}
    requests = [time(), time()] # bit of safety, assuming that creating the game is one API call but you never know.
    pending = None

    with open(bestfile) as f:
        for line in f:
            city, score = line.split()
            bestpermap[city] = float(score)

    if not os.path.exists("my_games"):
        print(f"Creating folder {game_folder}")
        os.makedirs(game_folder)

    try:
        with open('.secrets') as f:
            api_key = f.readline()
    except Exception as e:
        raise SystemExit("Did you forget to create a .env file with the apiKey?")

    # User selct a map name
    print(f"1: {MN.stockholm}")
    print(f"2: {MN.goteborg}")
    print(f"3: {MN.malmo}")
    print(f"4: {MN.uppsala}")
    print(f"5: {MN.vasteras}")
    print(f"6: {MN.orebro}")
    print(f"7: {MN.london}")
    print(f"8: {MN.berlin}")
    print(f"9: {MN.linkoping}")
    print(f"10: {MN.sSandbox}")
    print(f"11: {MN.gSandbox}")
    option_ = input("Select the map you wish to play: ")

    mapName = None
    match option_:
        case "1":
            mapName = MN.stockholm
        case "2":
            mapName = MN.goteborg
        case "3":
            mapName = MN.malmo
        case "4":
            mapName = MN.uppsala
        case "5":
            mapName = MN.vasteras
        case "6":
            mapName = MN.orebro
        case "7":
            mapName = MN.london
        case "8":
            mapName = MN.berlin
        case "9":
            mapName = MN.linkoping
        case "10":
            mapName = MN.sSandbox
        case "11":
            mapName = MN.gSandbox
        case _:
            print("Invalid choice.")

    if mapName:
        ##Get map data from Considition endpoint
        mapEntity = getMapData(mapName, api_key)
        ##Get non map specific data from Considition endpoint
        generalData = getGeneralData()

        map_record = 0 if mapName not in bestpermap else bestpermap[mapName]

        if mapEntity and generalData:
            # ------------------------------------------------------------
            # ----------------Player Algorithm goes here------------------
            solution = {LK.locations: {}}
            print(f'Number of locations is: {len(mapEntity[LK.locations])}')

            for key in mapEntity[LK.locations]:
                location = mapEntity[LK.locations][key]
                name = location[LK.locationName]

                solution[LK.locations][name] = {
                        LK.f9100Count: 1,
                        LK.f3100Count: 1,
                    }
                
            best_score = calculateScore(mapName, solution, mapEntity, generalData)[SK.gameScore][SK.total]
            best_solution = deepcopy(solution)

            def post_score(sco, best_score, best_solution):
                print(f'We achieved a new record of {best_score} for {mapName} and will now record it.')
                bestpermap[mapName] = best_score

                id_ = sco[SK.gameId]
                print(f"Storing game with id {id_}.")
                print(f"Enter {id_} into visualization.ipynb for local vizualization ")

                # Store solution locally for visualization
                with open(f"{game_folder}/{id_}.json", "w", encoding="utf8") as f:
                    json.dump(sco, f, indent=4)

                # Submit and and get score from Considition app
                print(f"Submitting solution to Considtion 2023 \n")

                scoredSolution = submit(mapName, best_solution, api_key)
                if scoredSolution:
                    print("Successfully submitted game")
                    print(f"id: {scoredSolution[SK.gameId]}")
                    print(f"Score: {scoredSolution[SK.gameScore]}")

                    with open(bestfile, 'w') as g:
                        for k, v in bestpermap.items():
                            g.write(f'{k} {v}\n')

            while True:
                if pending and time() - requests[0] > max_requests_time:
                    post_score(*pending)
                    requests = requests[1:] + [time()]
                    pending = None

                repeat = False

                for key in mapEntity[LK.locations]:
                    location = mapEntity[LK.locations][key]
                    name = location[LK.locationName]
                    
                    working_solution = deepcopy(best_solution)

                    for bigcount in range(max_locations + 1):
                        for smallcount in range(max_locations + 1):
                            iteration_solution = deepcopy(working_solution)

                            if bigcount == smallcount == 0:
                                if name in iteration_solution[LK.locations]:
                                    del iteration_solution[LK.locations][name]
                            else:
                                iteration_solution[LK.locations][name] = {
                                    LK.f9100Count: bigcount,
                                    LK.f3100Count: smallcount
                                }

                            sco = calculateScore(mapName, iteration_solution, mapEntity, generalData)
                            iteration_score = sco[SK.gameScore][SK.total]

                            if iteration_score > best_score:
                                print(f'When working on {name} we improved the score from {best_score} to {iteration_score}')
                                best_score = iteration_score
                                best_solution = deepcopy(iteration_solution)
                                repeat = True

                                if best_score > map_record:
                                    map_record = best_score

                                    if len(requests) < max_requests or time()-max_requests[0] > max_requests_time:
                                        t = time()

                                        if len(requests) == max_requests:
                                            requests = requests[1:] + [t]
                                        else:
                                            requests.append(t)

                                        post_score(sco, best_score, best_solution)
                                    else:
                                        pending = (deepcopy(sco), deepcopy(best_score), deepcopy(best_solution))

                if not repeat:
                    break

            if pending and time() - requests[0] > max_requests_time:
                post_score(*pending)
                requests = requests[1:] + [time()]
                pending = None

            print('ending game')

if __name__ == "__main__":
    main()
