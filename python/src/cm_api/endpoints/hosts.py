# Licensed to Cloudera, Inc. under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  Cloudera, Inc. licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

try:
  import json
except ImportError:
  import simplejson as json

from cm_api.endpoints.types import ApiList, BaseApiObject, \
    config_to_json, json_to_config

__docformat__ = "epytext"

HOSTS_PATH = "/hosts"

def create_host(resource_root, host_id, name, ipaddr, rack_id=None):
  """
  Create a host
  @param resource_root: The root Resource object.
  @param host_id: Host id
  @param name: Host name
  @param ipaddr: IP address
  @param rack_id: Rack id. Default None
  @return: An ApiHost object
  """
  apihost = ApiHost(resource_root, host_id, name, ipaddr, rack_id)
  apihost_list = ApiList([apihost])
  body = json.dumps(apihost_list.to_json_dict())
  resp = resource_root.post(HOSTS_PATH, data=body)
  # The server returns a list of created hosts (with size 1)
  return ApiList.from_json_dict(ApiHost, resp, resource_root)[0]

def get_host(resource_root, host_id):
  """
  Lookup a host by id
  @param resource_root: The root Resource object.
  @param host_id: Host id
  @return: An ApiHost object
  """
  dic = resource_root.get("%s/%s" % (HOSTS_PATH, host_id))
  return ApiHost.from_json_dict(dic, resource_root)

def get_all_hosts(resource_root, view=None):
  """
  Get all hosts
  @param resource_root: The root Resource object.
  @return: A list of ApiHost objects.
  """
  dic = resource_root.get(HOSTS_PATH,
          params=view and dict(view=view) or None)
  return ApiList.from_json_dict(ApiHost, dic, resource_root)

def delete_host(resource_root, host_id):
  """
  Delete a host by id
  @param resource_root: The root Resource object.
  @param host_id: Host id
  @return: The deleted ApiHost object
  """
  resp = resource_root.delete("%s/%s" % (HOSTS_PATH, host_id))
  return ApiHost.from_json_dict(resp, resource_root)


class ApiHost(BaseApiObject):
  RO_ATTR = ('status', 'lastHeartbeat', 'roleRefs', 'healthSummary',
      'healthChecks', 'hostUrl')
  RW_ATTR = ('hostId', 'hostname', 'ipAddress', 'rackId')

  def __init__(self, resource_root, hostId, hostname,
      ipAddress=None, rackId=None):
    # Note about "ipAddress = None":
    #
    # This generally happens when you bring up SCM and it gets an
    # "optimized" heartbeat from an agent, and you query the host info
    # before it's fully constructed. The JSON returned wouldn't have
    # the ipAddress field, and a TypeError would be raised.
    BaseApiObject.ctor_helper(**locals())

  def _path(self):
    return HOSTS_PATH + '/' + self.hostId

  def get_config(self, view=None):
    """
    Retrieve the host's configuration.

    The 'summary' view contains strings as the dictionary values. The full
    view contains ApiConfig instances as the values.

    @param view: View to materialize ('full' or 'summary')
    @return Dictionary with configuration data.
    """
    path = self._path() + '/config'
    resp = self._get_resource_root().get(path,
        params = view and dict(view=view) or None)
    return json_to_config(resp, view == 'full')

  def update_config(self, config):
    """
    Update the host's configuration.

    @param config Dictionary with configuration to update.
    @return Dictionary with updated configuration.
    """
    path = self._path() + '/config'
    resp = self._get_resource_root().put(path, data = config_to_json(config))
    return json_to_config(resp)

  def get_metrics(self, from_time=None, to_time=None, metrics=None,
      ifs=[], storageIds=[], view=None):
    """
    Retrieve metric readings for the host.

    @param from_time: A datetime; start of the period to query (optional).
    @param to_time: A datetime; end of the period to query (default = now).
    @param metrics: List of metrics to query (default = all).
    @param ifs: network interfaces to query. Default all, use None to disable.
    @param storageIds: storage IDs to query. Default all, use None to disable.
    @param view: View to materialize ('full' or 'summary')
    @return List of metrics and their readings.
    """
    params = { }
    if ifs:
      params['ifs'] = ifs
    elif ifs is None:
      params['queryNw'] = 'false'
    if storageIds:
      params['storageIds'] = storageIds
    elif storageIds is None:
      params['queryStorage'] = 'false'
    return self._get_resource_root().get_metrics(self._path() + '/metrics',
        from_time, to_time, metrics, view, params)
