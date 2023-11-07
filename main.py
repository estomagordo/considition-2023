import os
import json
from copy import deepcopy
from scoring import calculateScore
from api import getGeneralData, getMapData, submit
from data_keys import (
    MapNames as MN,
    LocationKeys as LK,
    ScoringKeys as SK,
)

api_key = ''
game_folder = "my_games"


def main():
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
        case _:
            print("Invalid choice.")

    if mapName:
        ##Get map data from Considition endpoint
        mapEntity = getMapData(mapName, api_key)
        ##Get non map specific data from Considition endpoint
        generalData = getGeneralData()

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

            while True:
                repeat = False

                for key in mapEntity[LK.locations]:
                    location = mapEntity[LK.locations][key]
                    name = location[LK.locationName]
                    
                    working_score = 0
                    working_solution = deepcopy(best_solution)

                    for bigcount in range(6):
                        for smallcount in range(6):
                            iteration_solution = deepcopy(working_solution)

                            if bigcount == smallcount == 0:
                                if name in iteration_solution[LK.locations]:
                                    del iteration_solution[LK.locations][name]
                            else:
                                iteration_solution[LK.locations][name] = {
                                    LK.f9100Count: bigcount,
                                    LK.f3100Count: smallcount
                                }

                            iteration_score = calculateScore(mapName, iteration_solution, mapEntity, generalData)[SK.gameScore][SK.total]

                            if iteration_score > working_score:
                                working_score = iteration_score
                                working_solution = deepcopy(iteration_solution)

                    if working_score > best_score:
                        print(f'When working on {name} we improved the score from {best_score} to {working_score}')
                        best_score = working_score
                        best_solution = deepcopy(working_solution)
                        repeat = True
                        break

                if not repeat:
                    break

            # ----------------End of player code--------------------------
            # ------------------------------------------------------------

            # Score solution locally
            score = calculateScore(mapName, best_solution, mapEntity, generalData)

            id_ = score[SK.gameId]
            print(f"Storing  game with id {id_}.")
            print(f"Enter {id_} into visualization.ipynb for local vizualization ")

            # Store solution locally for visualization
            with open(f"{game_folder}/{id_}.json", "w", encoding="utf8") as f:
                json.dump(score, f, indent=4)

            # Submit and and get score from Considition app
            print(f"Submitting solution to Considtion 2023 \n")

            scoredSolution = submit(mapName, solution, api_key)
            if scoredSolution:
                print("Successfully submitted game")
                print(f"id: {scoredSolution[SK.gameId]}")
                print(f"Score: {scoredSolution[SK.gameScore]}")


if __name__ == "__main__":
    main()
