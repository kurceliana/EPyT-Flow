import sys
sys.path.insert(0,'..')
import numpy as np

from epyt_flow.data.networks import load_hanoi
from epyt_flow.simulation import WaterDistributionNetworkScenarioSimulator

from utils import get_temp_folder


def test_sensor_readings():
    hanoi_network_config = load_hanoi(download_dir=get_temp_folder(),
                                      include_default_sensor_placement=True)
    with WaterDistributionNetworkScenarioSimulator(scenario_config=hanoi_network_config) as sim:
        sim.set_general_parameters(simulation_duration=2)
        sim.randomize_demands()

        res = sim.run_simulation()

        assert len(res.get_data_pressures()) != 0
        assert len(res.get_data_flows()) != 0

        assert len(res.get_data_pressures(sensor_locations=
                                          [res.sensor_config.pressure_sensors[0]])) != 0
        assert len(res.get_data_flows(sensor_locations=
                                      [res.sensor_config.flow_sensors[0]])) != 0
