import asyncio
from typing import Any, cast, Set, Union

from tools.components import AbstractSimulationComponent
from tools.exceptions.messages import MessageError
from tools.messages import BaseMessage
from tools.tools import FullLogger, load_environmental_variables, log_exception

# import all the required messages from installed libraries
from user_component.car_metadata_message import CarMetaDataMessage
from user_component.car_state_message import CarStateMessage
from user_component.user_state_message import UserStateMessage
from datetime import datetime

# initialize logging object for the module
LOGGER = FullLogger(__name__)


# set the names of the used environment variables to Python variables
USER_ID = "USER_ID"
USER_NAME = "USER_NAME"
STATION_ID = "STATION_ID"
STATE_OF_CHARGE = "STATE_OF_CHARGE"
CAR_BATTERY_CAPACITY = "CAR_BATTERY_CAPACITY"
CAR_MODEL = "CAR_MODEL"
CAR_MAX_POWER = "CAR_MAX_POWER"
TARGET_STATE_OF_CHARGE = "TARGET_STATE_OF_CHARGE"
TARGET_TIME = "TARGET_TIME"

INPUT_COMPONENTS = "INPUT_COMPONENTS"
OUTPUT_DELAY = "OUTPUT_DELAY"

USER_STATE_TOPIC = "USER_STATE_TOPIC"
CAR_STATE_TOPIC = "CAR_STATE_TOPIC"
CAR_METADATA_TOPIC = "USER_STATE_TOPIC"


# time interval in seconds on how often to check whether the component is still running
TIMEOUT = 1.0


class UserComponent(AbstractSimulationComponent):
    # The constructor for the component class.
    def __init__(
        self,
        user_id: int,
        user_name: str,
        station_id: int,
        state_of_charge: float,
        car_battery_capacity: float,
        car_model: str,
        car_max_power: float,
        target_state_of_charge: float,
        target_time: datetime,
        input_components: Set[str],
        output_delay: float):
        
        # Initialize the AbstractSimulationComponent using the values from the environmental variables.
        # This will initialize various variables including the message client for message bus access.    
        super().__init__()
    
        # Set the object variables for the extra parameters.
        self._user_id = user_id
        self._user_name = user_name
        self._station_id = station_id
        self._state_of_charge = state_of_charge
        self._car_battery_capacity = car_battery_capacity
        self._car_model = car_model
        self._car_max_power = car_max_power
        self._target_state_of_charge = target_state_of_charge
        self._target_time = target_time

        # Add checks for the parameters if necessary
        # and set initialization error if there is a problem with the parameters.
        # if <some_check_for_the_parameters>:
        #     # add appropriate error message
        #     self.initialization_error = "There was a problem with the parameters"
        #     LOGGER.error(self.initialization_error)

        # variables to keep track of the components that have provided input within the current epoch
        # and to keep track of the current sum of the input values

        self._current_input_components = set()


        # Load environmental variables for those parameters that were not given to the constructor.
        # In this template the used topics are set in this way with given default values as an example.

        environment = load_environmental_variables(
            (USER_STATE_TOPIC, str, "UserStateTopic"),
            (CAR_STATE_TOPIC, str, "CarStateTopic"),
            (CAR_METADATA_TOPIC, str, "CarMetadataTopic")
        )

        
        
