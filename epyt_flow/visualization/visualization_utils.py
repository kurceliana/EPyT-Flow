from dataclasses import dataclass
import numpy as np
from typing import Optional, Union, List, Tuple, Iterable
import inspect
import networkx.drawing.nx_pylab as nxp
import matplotlib as mpl
from scipy.interpolate import CubicSpline

from epyt_flow.simulation.scada.scada_data import ScadaData
from ..serialization import COLOR_SCHEMES_ID, JsonSerializable, serializable

stat_funcs = {
        'mean': np.mean,
        'min': np.min,
        'max': np.max
    }


@dataclass
class JunctionObject:
    nodelist: list
    pos: dict
    node_shape: mpl.path.Path = None
    node_size: int = 10
    node_color: Union[str, list] = 'k' # list of lists with frames or single letter
    interpolated: bool = False

    def add_frame(self, statistic: str, values: np.ndarray,
                                pit: Union[int, Tuple[int]],
                                intervals: Union[int, List[Union[int, float]]]):

        if statistic in stat_funcs:
            stat_values = stat_funcs[statistic](values, axis=0)
        elif statistic == 'time_step':
            if not pit and pit != 0:
                raise ValueError(
                    'Please input point in time (pit) parameter when selecting'
                    ' time_step statistic')
            stat_values = np.take(values, pit, axis=0)
        else:
            raise ValueError(
                'Statistic parameter must be mean, min, max or time_step')

        if intervals is None:
            pass
        elif isinstance(intervals, (int, float)):
            interv = np.linspace(stat_values.min(), stat_values.max(),
                                 intervals + 1)
            stat_values = np.digitize(stat_values, interv) - 1
        elif isinstance(intervals, list):
            stat_values = np.digitize(stat_values, intervals) - 1
        else:
            raise ValueError(
                'Intervals must be either number of groups or list of interval'
                ' boundary points')

        # TODO self.nodelist oder sensor config nodes?? Je nachdem ob es eine sensor_config gibt?
        sorted_values = [v for _, v in zip(self.nodelist, stat_values)]

        if isinstance(self.node_color, str):
            # First run of this method
            self.node_color = []
            self.vmin = min(sorted_values)
            self.vmax = max(sorted_values)

        self.node_color.append(sorted_values)
        self.vmin = min(*sorted_values, self.vmin)
        self.vmax = max(*sorted_values, self.vmin)

    def get_frame(self, frame_number: int = 0):

        attributes = vars(self).copy()

        if not isinstance(self.node_color, str):
            if self.interpolated:
                if frame_number > len(self.node_color_inter):
                    frame_number = -1
                attributes['node_color'] = self.node_color_inter[frame_number]
            else:
                if frame_number > len(self.node_color):
                    frame_number = -1
                attributes['node_color'] = self.node_color[frame_number]

        sig = inspect.signature(nxp.draw_networkx_nodes)

        valid_params = {
            key: value for key, value in attributes.items()
            if key in sig.parameters and value is not None
        }

        return valid_params

    def interpolate(self, num_inter_frames):
        if isinstance(self.node_color, str) or len(self.node_color) <= 1:
            return

        tmp_node_color = np.array(self.node_color)
        steps, num_nodes = tmp_node_color.shape

        x_axis = np.linspace(0, steps - 1, steps)
        new_x_axis = np.linspace(0, steps - 1, num_inter_frames)

        self.node_color_inter = np.zeros(((len(new_x_axis)), num_nodes))

        for node in range(num_nodes):
            cs = CubicSpline(x_axis, tmp_node_color[:, node])
            self.node_color_inter[:, node] = cs(new_x_axis)

        self.interpolated = True

    def add_attributes(self, attributes: dict):
        for key, value in attributes.items():
            setattr(self, key, value)


@dataclass
class EdgeObject:
    edgelist: list
    pos: dict
    edge_color: Union[str, list] = 'k' # list of lists with frames or single letter
    interpolated = {}

    def rescale_widths(self, line_widths: Tuple[int] = (1, 2)):
        if not hasattr(self, 'width'):
            raise AttributeError("Please call add_frame with edge_param=width before rescaling the widths.")

        vmin = min(min(l) for l in self.width)
        vmax = max(max(l) for l in self.width)

        tmp = []
        for il in self.width:
            tmp.append(self.__rescale(il, line_widths, values_min_max=(vmin, vmax)))
        self.width = tmp

    def add_frame(
            self, topology, edge_param: str, scada_data: Optional[ScadaData] = None,
            parameter: str = 'flow_rate', statistic: str = 'mean',
            pit: Optional[Union[int, Tuple[int]]] = None,
            intervals: Optional[Union[int, List[Union[int, float]]]] = None):

        if edge_param == 'edge_width' and not hasattr(self, 'width'):
            self.width = []
        elif edge_param == 'edge_color':
            if isinstance(self.edge_color, str):
                self.edge_color = []
                self.edge_vmin = float('inf')
                self.edge_vmax = float('-inf')

        if parameter == 'flow_rate':
            values = scada_data.flow_data_raw
        elif parameter == 'link_quality':
            values = scada_data.link_quality_data_raw
        elif parameter == 'custom_data':
            values = scada_data
        elif parameter == 'diameter':
            value_dict = {
                link[0]: topology.get_link_info(link[0])['diameter'] for
                link in topology.get_all_links()}
            sorted_values = [value_dict[x[0]] for x in
                             topology.get_all_links()]

            if edge_param == 'edge_width':
                self.width.append(sorted_values)
            else:
                self.edge_color.append(sorted_values)
                self.edge_vmin = min(*sorted_values, self.edge_vmin)
                self.edge_vmax = max(*sorted_values, self.edge_vmax)

            return
        else:
            raise ValueError('Parameter must be flow_rate or link_quality')

        if statistic in stat_funcs:
            stat_values = stat_funcs[statistic](values, axis=0)
        elif statistic == 'time_step':
            if not pit and pit != 0:
                raise ValueError(
                    'Please input point in time (pit) parameter when selecting'
                    ' time_step statistic')
            stat_values = np.take(values, pit, axis=0)
        else:
            raise ValueError(
                'Statistic parameter must be mean, min, max or time_step')

        if intervals is None:
            pass
        elif isinstance(intervals, (int, float)):
            interv = np.linspace(stat_values.min(), stat_values.max(),
                                 intervals + 1)
            stat_values = np.digitize(stat_values, interv) - 1
        elif isinstance(intervals, list):
            stat_values = np.digitize(stat_values, intervals) - 1
        else:
            raise ValueError(
                'Intervals must be either number of groups or list of interval'
                ' boundary points')

        sorted_values = list(stat_values)

        if edge_param == 'edge_width':
            self.width.append(sorted_values)
        else:
            self.edge_color.append(sorted_values)
            self.edge_vmin = min(*sorted_values, self.edge_vmin)
            self.edge_vmax = max(*sorted_values, self.edge_vmax)

    def get_frame(self, frame_number: int = 0):

        attributes = vars(self).copy()

        if not isinstance(self.edge_color, str):
            if 'edge_color' in self.interpolated.keys():
                if frame_number > len(self.interpolated['edge_color']):
                    frame_number = -1
                attributes['edge_color'] = self.interpolated['edge_color'][frame_number]
            else:
                if frame_number > len(self.edge_color):
                    frame_number = -1
                attributes['edge_color'] = self.edge_color[frame_number]

        if hasattr(self, 'width'):
            if 'width' in self.interpolated.keys():
                if frame_number > len(self.interpolated['width']):
                    frame_number = -1
                attributes['width'] = self.interpolated['width'][frame_number]
            else:
                if frame_number > len(self.width):
                    frame_number = -1
                attributes['width'] = self.width[frame_number]

        sig = inspect.signature(nxp.draw_networkx_edges)

        valid_params = {
            key: value for key, value in attributes.items()
            if key in sig.parameters and value is not None
        }

        return valid_params

    def interpolate(self, num_inter_frames):

        targets = {'edge_color': self.edge_color}
        if hasattr(self, 'width'):
            targets['width'] = self.width

        for name, inter_target in targets.items():
            if isinstance(inter_target, str) or len(inter_target) <= 1:
                continue

            tmp_target = np.array(inter_target)
            steps, num_edges = tmp_target.shape

            x_axis = np.linspace(0, steps - 1, steps)
            new_x_axis = np.linspace(0, steps - 1, num_inter_frames)

            vals_inter = np.zeros(((len(new_x_axis)), num_edges))

            for edge in range(num_edges):
                cs = CubicSpline(x_axis, tmp_target[:, edge])
                vals_inter[:, edge] = cs(new_x_axis)

            self.interpolated[name] = vals_inter

    def add_attributes(self, attributes: dict):
        for key, value in attributes.items():
            setattr(self, key, value)

    @staticmethod
    def __rescale(values: np.ndarray, scale_min_max: List,
                  values_min_max: List = None) -> List:
        """
        Rescales the given values to a new range.

        This method rescales an array of values to fit within a specified
        minimum and maximum scale range. Optionally, the minimum and maximum
        of the input values can be manually provided; otherwise, they are
        automatically determined from the data.

        Parameters
        ----------
        values : :class:`~np.ndarray`
            The array of numerical values to be rescaled.
        scale_min_max : `list`
            A list containing two elements: the minimum and maximum values
            of the desired output range.
        values_min_max : `list`, optional
            A list containing two elements: the minimum and maximum values
            of the input data. If not provided, they are computed from the
            input `values`. Default is `None`.

        Returns
        -------
        rescaled_values : `list`
            A list of values rescaled to the range specified by
            `scale_min_max`.

        """

        if not values_min_max:
            min_val, max_val = min(values), max(values)
        else:
            min_val, max_val = values_min_max
        scale = scale_min_max[1] - scale_min_max[0]

        def range_map(x):
            return scale_min_max[0] + (x - min_val) / (
                    max_val - min_val) * scale

        return [range_map(x) for x in values]


@serializable(COLOR_SCHEMES_ID, ".epyt_flow_color_schemes")
class ColorScheme(JsonSerializable):
    EPANET = {
        "pipe_color": "#0403ee",
        "node_color": "#0403ee",
        "pump_color": "#fe00ff",
        "tank_color": "#02fffd",
        "reservoir_color": "#00ff00",
        "valve_color": "#000000",
    }
    EPYT_FLOW = {
        "pipe_color": "#29222f",
        "node_color": "#29222f",
        "pump_color": "#d79233",
        "tank_color": "#607b80",
        "reservoir_color": "#33483d",
        "valve_color": "#a3320b",
    }
    BLACK = {
        "pipe_color": "#000000",
        "node_color": "#000000",
        "pump_color": "#000000",
        "tank_color": "#000000",
        "reservoir_color": "#000000",
        "valve_color": "#000000",
    }

    def __init__(self):
        super().__init__()

    def get_attributes(self):
        attr = {
            k: v for k, v in self.__class__.__dict__.items()
            if not k.startswith("__") and not callable(v)
        }
        return super().get_attributes() | attr
