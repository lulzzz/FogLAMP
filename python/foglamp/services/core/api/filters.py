# -*- coding: utf-8 -*-

# FOGLAMP_BEGIN
# See: http://foglamp.readthedocs.io/
# FOGLAMP_END

import datetime
import json
from aiohttp import web
from foglamp.common.storage_client.payload_builder import PayloadBuilder
from foglamp.common.configuration_manager import ConfigurationManager
from foglamp.services.core import server
from foglamp.services.core import connect
from foglamp.services.core.scheduler.entities import Schedule, TimedSchedule, IntervalSchedule, ManualSchedule
from foglamp.common.storage_client.exceptions import StorageServerError
from foglamp.common import utils
from foglamp.services.core.api import utils as apiutils
from foglamp.common import logger

__author__ = "Massimiliano Pinto"
__copyright__ = "Copyright (c) 2018 OSIsoft, LLC"
__license__ = "Apache 2.0"
__version__ = "${VERSION}"

_help = """
    -----------------------------------------------------------------------
    | POST            | /foglamp/filter                               |
    -----------------------------------------------------------------------
"""

_LOGGER = logger.setup("filter")

async def add_filter(request):
    """
    Create a new filter with a specific plugin
    
    :Example:
     curl -X POST http://localhost:8081/foglamp/filter -d 
     '{
        "name": "North_Readings_to_PI_scale_stage_1Filter",
        "plugin": "scale"
     }'

    'name' is the filter name
    'plugin' is the filter plugin name

    The plugin is loaded and default comnfg from 'plugin_info'
    is fetched.

    A new config category 'name' is created:
    items are:
       - 'plugin'
       - all ityems from default plugin config

    NOTE: The 'create_category' call is made with keep_original_items = True

    """
    try:
        data = await request.json()
        filter_name = data.get('name')
        plugin_name = data.get('plugin')
        filter_desc = 'Configuration of \'' + filter_name + '\' filter for plugin \'' + plugin_name + '\'' 

        # Get configuration manager instance
        cf_mgr = ConfigurationManager(connect.get_storage_async())

        # Load the specified plugin and get plugin data
        loaded_plugin_info = apiutils.get_plugin_info(plugin_name)

        # Get plugin default configuration (dict)
        plugin_config = loaded_plugin_info['config']

        # Get plugin type (string)
        loaded_plugin_type = loaded_plugin_info['type'];

        # Get plugin name (string)
        loaded_plugin_name = plugin_config['plugin']['default'];

        # Sanity checks
        if (plugin_name != loaded_plugin_name or loaded_plugin_type != 'filter'):
             errorMessage = "Loaded plugin '" + loaded_plugin_name + \
                            "', type '" + loaded_plugin_type + \
                            "', doesn't match the specified one '" + \
                            plugin_name + "', type 'filter'"
             raise Exception(errorMessage)

        #################################################
        # Set string value for 'default' if type is JSON
        # This is required by the configuration manager
        ################################################# 
        for key, value in plugin_config.items():
            if (value['type'] == 'JSON'):
                value['default'] = json.dumps(value['default'])

        await cf_mgr.create_category(category_name=filter_name,
                                     category_description=filter_desc,
                                     category_value=plugin_config,
                                     keep_original_items=True)

        # Fetch the new created filter: get category items
        category_info = await cf_mgr.get_category_all_items(category_name = filter_name)
        if category_info is None:
            message = "No such '%s' filter found" % filter_name
            raise Exception(message)

    except Exception as ex:
        _LOGGER.error("Caught exception: " + str(ex))
        raise web.HTTPInternalServerError(reason=str(ex))

    return web.json_response({'filter': filter_name,
                              'description': filter_desc,
                              'value': category_info})

