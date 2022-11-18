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
CAR_METADATA_TOPIC = "CAR_METADATA_TOPIC"


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
        target_time: str,
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
        # fix topic names
        environment = load_environmental_variables(
            (USER_STATE_TOPIC, str, "User.UserState"),
            (CAR_STATE_TOPIC, str, "User.CarState"),
            (CAR_METADATA_TOPIC, str, "Init.User.CarMetadata")
        )

        self._user_state_topic_base = cast(str, environment[USER_STATE_TOPIC])
        # self._user_state_topic_output = ".".join([self._user_state_topic_base, self.component_name])

        self._car_state_topic_base = cast(str, environment[CAR_STATE_TOPIC])
        self._car_state_topic_output = ".".join([self._car_state_topic_base, self.component_name])

        self._car_metadata_topic_base = cast(str, environment[CAR_METADATA_TOPIC])
        self._car_metadata_topic_output = ".".join([self._car_metadata_topic_base, self.component_name])     

        # The easiest way to ensure that the component will listen to all necessary topics
        # is to set the self._other_topics variable with the list of the topics to listen to.
        # Note, that the "SimState" and "Epoch" topic listeners are added automatically by the parent class.
        
        #recieve topic
        self._other_topics = [
            "Station.PowerOutput"
        ]

        # The base class contains several variables that can be used in the child class.
        # The variable list below is not an exhaustive list but contains the most useful variables.

        # Variables that should only be READ in the child class:
        # - self.simulation_id               the simulation id
        # - self.component_name              the component name
        # - self._simulation_state           either "running" or "stopped"
        # - self._latest_epoch               epoch number for the current epoch
        # - self._completed_epoch            epoch number for the latest epoch that has been completed
        # - self._latest_epoch_message       the latest epoch message as EpochMessage object

        # Variable for the triggering message ids where all relevant message ids should be appended.
        # The list is automatically cleared at the start of each epoch.
        # - self._triggering_message_ids

        # MessageGenerator object that can be used to generate the message objects:
        # - self._message_generator

        # RabbitmqClient object for communicating with the message bus:
        # - self._rabbitmq_client

    def clear_epoch_variables(self) -> None:
        """Clears all the variables that are used to store information about the received input within the
           current epoch. This method is called automatically after receiving an epoch message for a new epoch.
           NOTE: this method should be overwritten in any child class that uses epoch specific variables
        """
        self._current_input_components = set()

    async def process_epoch(self) -> bool:
        """
        Process the epoch and do all the required calculations.
        Assumes that all the required information for processing the epoch is available.
        Returns False, if processing the current epoch was not yet possible.
        Otherwise, returns True, which indicates that the epoch processing was fully completed.
        This also indicated that the component is ready to send a Status Ready message to the Simulation Manager.
        NOTE: this method should be overwritten in any child class.
        TODO: add proper description specific for this component.
        """

        # send the output message
        await asyncio.sleep(self._output_delay)

        # Modify with Conditions
        ## Add the send message functions
        await self._send_car_metadata_message()
        await self._send_user_state_message()
        await self._send_car_state_message()

        #Modify
        # return True to indicate that the component is finished with the current epoch
        return True


    async def all_messages_received_for_epoch(self) -> bool:
        """
        Returns True, if all the messages required to start calculations for the current epoch have been received.
        Checks only that all the required information is available.
        Does not check any other conditions like the simulation state.
        NOTE: this method should be overwritten in any child class that needs more
        information than just the Epoch message.
        TODO: add proper description specific for this component.
        """
        return self._input_components == self._current_input_components


    async def general_message_handler(self, message_object: Union[BaseMessage, Any], message_routing_key: str) -> None:
        """
        Handles the incoming messages. message_routing_key is the topic for the message.
        Assumes that the messages are not of type SimulationStateMessage or EpochMessage.
        NOTE: this method should be overwritten in any child class that
        listens to messages other than SimState or Epoch messages.
        TODO: add proper description specific for this component.
        
        
        """
        # Replace by incoming station message
        if isinstance(message_object, UserStateMessage):
            # added extra cast to allow Pylance to recognize that message_object is an instance of UserStateMessage
            message_object = cast(UserStateMessage, message_object)
            # ignore simple messages from components that have not been registered as input components
            if message_object.source_process_id not in self._input_components:
                LOGGER.debug(f"Ignoring UserStateMessage from {message_object.source_process_id}")

            # only take into account the first simple message from each component
            elif message_object.source_process_id in self._current_input_components:
                LOGGER.info(f"Ignoring new UserStateMessage from {message_object.source_process_id}")

            else:
                self._current_input_components.add(message_object.source_process_id)
                LOGGER.debug(f"Received UserStateMessage from {message_object.source_process_id}")

                self._triggering_message_ids.append(message_object.message_id)
                if not await self.start_epoch():
                    LOGGER.debug(f"Waiting for other input messages before processing epoch {self._latest_epoch}")

        else:
            LOGGER.debug("Received unknown message from {message_routing_key}: {message_object}")

    async def _send_user_state_message(self):

        try:
            user_state_message = self._message_generator.get_message(
                UserStateMessage,
                EpochNumber=self._latest_epoch,
                TriggeringMessageIds=self._triggering_message_ids,
                UserId=self._user_id,
                TargetStateOfCharge=self._target_state_of_charge,
                TargetTime=self._target_time
            )

            await self._rabbitmq_client.send_message(
                topic_name=self._user_state_topic_output,
                message_bytes= user_state_message.bytes()
            )

        except (ValueError, TypeError, MessageError) as message_error:
            # When there is an exception while creating the message, it is in most cases a serious error.
            log_exception(message_error)
            await self.send_error_message("Internal error when creating result message.")

    async def _send_car_state_message(self):

        try:
            car_state_message = self._message_generator.get_message(
                CarStateMessage,
                EpochNumber=self._latest_epoch,
                TriggeringMessageIds=self._triggering_message_ids,
                UserId=self._user_id,
                StationId=self._station_id,
                StateOfCharge=self._state_of_charge
            )

            await self._rabbitmq_client.send_message(
                topic_name=self._car_state_topic_output,
                message_bytes= car_state_message.bytes()
            )

        except (ValueError, TypeError, MessageError) as message_error:
            # When there is an exception while creating the message, it is in most cases a serious error.
            log_exception(message_error)
            await self.send_error_message("Internal error when creating result message.")

    async def _send_car_metadata_message(self):

        try:
            car_metadata_message = self._message_generator.get_message(
                CarMetaDataMessage,
                EpochNumber=self._latest_epoch,
                TriggeringMessageIds=self._triggering_message_ids,
                UserId=self._user_id,
                UserName=self._user_name,
                StationId=self._station_id,
                StateOfCharge=self._state_of_charge,
                CarBatteryCapacity=self._car_battery_capacity,
                CarModel=self._car_model,
                CarMaxPower=self._car_max_power
            )

            await self._rabbitmq_client.send_message(
                topic_name=self._car_metadata_topic_output,
                message_bytes= car_metadata_message.bytes()
            )

        except (ValueError, TypeError, MessageError) as message_error:
            # When there is an exception while creating the message, it is in most cases a serious error.
            log_exception(message_error)
            await self.send_error_message("Internal error when creating result message.")

def create_component() -> UserComponent:
    """
    TODO: add proper description specific for this component.
    """

    # Read the parameters for the component from the environment variables.
    environment_variables = load_environmental_variables(
        (USER_ID, int, 0),   
        (USER_NAME, str, ""),
        (STATION_ID, int, 0),
        (STATE_OF_CHARGE, float, 0.0),
        (CAR_BATTERY_CAPACITY, float, 0.0),
        (CAR_MODEL, str, ""),
        (CAR_MAX_POWER, float, 0.0),
        (TARGET_STATE_OF_CHARGE, float, 0.0),
        (TARGET_TIME, str, ""),
        (INPUT_COMPONENTS, str, ""),  # the comma-separated list of component names that provide input
        (OUTPUT_DELAY, float, 0.0)    # delay in seconds before sending the result message for the epoch
    )


    # The cast function here is only used to help Python linters like pyright to recognize the proper type.
    # They are not necessary and can be omitted.
    user_id = cast(int, environment_variables[USER_ID])
    user_name = cast(str, environment_variables[USER_NAME])
    station_id = cast(int, environment_variables[STATION_ID])
    state_of_charge = cast(float, environment_variables[STATE_OF_CHARGE])
    car_battery_capacity = cast(float, environment_variables[CAR_BATTERY_CAPACITY])
    car_model = cast(str, environment_variables[CAR_MODEL])
    car_max_power = cast(str, environment_variables[CAR_MAX_POWER])
    target_state_of_charge = cast(str, environment_variables[TARGET_STATE_OF_CHARGE])
    target_time = cast(str, environment_variables[TARGET_TIME])

    # put the input components to a set, only consider component with non-empty names
    input_components = {
        input_component
        for input_component in cast(str, environment_variables[INPUT_COMPONENTS]).split(",")
        if input_component
    }
    output_delay = cast(float, environment_variables[OUTPUT_DELAY])

    # Create and return a new SimpleComponent object using the values from the environment variables
    return UserComponent(
        user_id = user_id,
        user_name = user_name,
        station_id = station_id,
        state_of_charge = state_of_charge,
        car_battery_capacity = car_battery_capacity,
        car_model = car_model,
        car_max_power = car_max_power,
        target_state_of_charge = ctarget_state_of_charge,
        target_time = target_time
    )

async def start_component():
    """
    Creates and starts a UserComponent component.
    """
    # A general exception handler that should catch any unhandled error that would otherwise crash the program.
    # Having this might be especially useful when testing components in large simulations and some component(s)
    # crash without giving any output.
    #
    # Note, that any exceptions thrown in async functions will not be caught here.
    # Instead they should get logged as warnings but otherwise should not crash the component.
    try:
        user_component = create_component()

        # The component will only start listening to the message bus once the start() method has been called.
        await user_component.start()

        # Wait in the loop until the component has stopped itself.
        while not user_component.is_stopped:
            await asyncio.sleep(TIMEOUT)

    except BaseException as error:  # pylint: disable=broad-except
        log_exception(error)
        LOGGER.info("Component will now exit.")


if __name__ == "__main__":
    asyncio.run(start_component())