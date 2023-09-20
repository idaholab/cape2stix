'''This script is intended to validate all files in the output directory.
Requires revision in the future'''

import os
import logging
import json
from tqdm import tqdm
from stix2validator import validate_instance, print_results
# pylint: disable=trailing-whitespace
# pylint: disable=invalid-name
# pylint: disable=logging-fstring-interpolation

logging.basicConfig(filename='validated.log', encoding='utf-8', level=logging.INFO)

directory = "output"
val = 0
inval = 0

for item in tqdm(os.listdir(directory)):
    try:
        if item != ".gitkeep":
            with open(os.path.join(directory, item)) as f:
                bundle = json.load(f)
                results = validate_instance(bundle)
                if not results.is_valid:
                    logging.error(f"{f} is not valid")
                    logging.debug(print_results(results))
                    inval += 1
                else:
                    val += 1
    except Exception as err:
        logging.error(f"Exception in file {directory}/{item}")
        logging.exception(err)


logging.info(f"Valid Files: {val}")
print(f"Valid Files: {val}")
logging.info(f"Invalid Files: {inval}")
print(f"Invalid Files: {inval}")
