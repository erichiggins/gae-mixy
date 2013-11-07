#!/usr/bin/env python
"""
AppStats serializer module.
"""

__author__ = 'Eric Higgins'
__copyright__ = 'Copyright 2013, Eric Higgins'
__version__ = '0.0.5'
__email__ = 'erichiggins@gmail.com'
__status__ = 'Development'


from google.appengine.ext.appstats import loader
from google.appengine.ext.appstats import recording


__all__ = [
    'appstats_to_dict',
    'load_summary_protos',
    'load_full_proto',
    'load_full_proto_from_timestamp',
    'request_stats_to_dict',
]


def FormatFixed32(value):
  """Local copy of proto.ProtocolMessage.FormatFixed32 function."""
  if (value < 0):
    value += (1L << 32)
  return '0x%x' % value


def FormatFixed64(value):
  """Local copy of proto.ProtocolMessage.FormatFixed64 function."""
  if (value < 0):
    value += (1L << 64)
  return '0x%x' % value


def iter_proto(pb, prop_name, dict_fn):
  """Iterate over a repeated proto property and convert all to dictionaries."""
  return [dict_fn(getattr(pb, prop_name)(i)) for i in xrange(getattr(pb, prop_name + '_size')())]


def billed_ops_to_dict(pb):
  """appstats.datastore_pb.BilledOpsProto converter."""
  return {
      'op': pb.op(),
      'num_ops': pb.num_ops(),
  }


def stack_frame_to_dict(pb):
  """appstats.datastore_pb.StackFrameProto converter."""
  return {
      'class_or_file_name': pb.class_or_file_name(),
      'line_number': pb.line_number(),
      'function_name': pb.function_name(),
      'variables': iter_proto(pb, 'variables', key_val_to_dict),
  }


def individual_rpc_stats_to_dict(pb):
  """appstats.datastore_pb.IndividualRpcStatsProto converter."""
  return {
      'service_call_name': pb.service_call_name(),
      'request_data_summary': pb.request_data_summary(),
      'response_data_summary': pb.response_data_summary(),
      'api_mcycles': pb.api_mcycles(),
      'api_milliseconds': pb.api_milliseconds(),
      'start_offset_milliseconds': pb.start_offset_milliseconds(),
      'duration_milliseconds': pb.duration_milliseconds(),
      'namespace': pb.namespace(),
      'was_successful': bool(pb.was_successful()),
      'call_stack': iter_proto(pb, 'call_stack', stack_frame_to_dict),
      'datastore_details': datastore_call_details_to_dict(pb.datastore_details()),
      'call_cost_microdollars': pb.call_cost_microdollars(),
      'billed_ops': iter_proto(pb, 'billed_ops', billed_ops_to_dict),
  }


def aggregate_rpc_stats_to_dict(pb):
  """appstats.datastore_pb.AggregateRpcStatsProto converter."""
  return {
      'service_call_name': pb.service_call_name(),
      'total_amount_of_calls': pb.total_amount_of_calls(),
      'total_cost_of_calls_microdollars': pb.total_cost_of_calls_microdollars(),
      'total_billed_ops': iter_proto(pb, 'total_billed_ops', billed_ops_to_dict),
  }


def key_val_to_dict(pb):
  """appstats.datastore_pb.KeyValProto converter."""
  return {pb.key(): pb.value()}


def datastore_call_details_to_dict(pb):
  """appstats.datastore_pb.DatastoreCallDetailsProto converter."""
  return {
      'query_kind': pb.query_kind(),
      'query_ancestor': reference_to_dict(pb.query_ancestor()),
      'query_thiscursor': FormatFixed64(pb.query_thiscursor()),
      'query_nextcursor': FormatFixed64(pb.query_nextcursor()),
  }


def path_element_to_dict(pb):
  """datastore.entity_pb.Path_Element converter."""
  return {
      'type': pb.type(),
      'id': pb.id(),
      'name': pb.name(),
  }


def reference_to_dict(pb):
  """datastore.entity_pb.Reference converter."""
  return {
      'app': pb.app(),
      'name_space': pb.name_space(),
      'path': iter_proto(pb.path(), 'element', path_element_to_dict),
  }


def request_stats_to_dict(pb):
  """appstats.datastore_pb.RequestStatsProto converter."""
  return {
      'start_timestamp_milliseconds': pb.start_timestamp_milliseconds(),
      'http_method': pb.http_method(),
      'http_path': pb.http_path(),
      'http_query': pb.http_query(),
      'http_status': pb.http_status(),
      'duration_milliseconds': pb.duration_milliseconds(),
      'api_mcycles': pb.api_mcycles(),
      'processor_mcycles': pb.processor_mcycles(),
      'rpc_stats': iter_proto(pb, 'rpc_stats', aggregate_rpc_stats_to_dict),
      'cgi_env': iter_proto(pb, 'cgi_env', key_val_to_dict),
      'overhead_walltime_milliseconds': pb.overhead_walltime_milliseconds(),
      'user_email': pb.user_email(),
      'is_admin': bool(pb.is_admin()),
      'individual_stats': iter_proto(pb, 'individual_stats', individual_rpc_stats_to_dict),
  }


def appstats_to_dict(filter_timestamp=0, summaries_only=False):
  """Pull all AppStats records from memcache and convert to dictionaries."""
  loader_fn = loader.FromMemcache
  if summaries_only:
    loader_fn = load_summary_protos
  return [request_stats_to_dict(x._proto) for x in loader_fn(filter_timestamp)]


def load_summary_protos(filter_timestamp=0):
  """Fetch only AppStats summary protos and filter by optional timestamp."""
  return [x for x in recording.load_summary_protos() if x.start_timestamp_milliseconds() > filter_timestamp]


def load_full_proto(summary):
  """Fetch a full detail AppStats from a summary proto."""
  return load_full_proto_from_timestamp(summary.start_timestamp_milliseconds())


def load_full_proto_from_timestamp(timestamp):
  """Fetch a full detail AppStats from a summary proto timestamp."""
  timestamp = int(timestamp) * 0.001
  return recording.load_full_proto(timestamp)
