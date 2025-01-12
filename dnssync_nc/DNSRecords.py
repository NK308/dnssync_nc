#	dnssync_nc - DNS API interface for the ISP netcup
#	Copyright (C) 2020-2022 Johannes Bauer
#
#	This file is part of dnssync_nc.
#
#	dnssync_nc is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation; this program is ONLY licensed under
#	version 3 of the License, later versions are explicitly excluded.
#
#	dnssync_nc is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	You should have received a copy of the GNU General Public License
#	along with dnssync_nc; if not, write to the Free Software
#	Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#	Johannes Bauer <JohannesBauer@gmx.de>

from typing import Optional, TypeVar, Any

TDNSRecord = TypeVar("TDNSRecord", bound="DNSRecord")

class DNSRecord():
	def __init__(self, record_id: Optional[int], record_type: str, hostname: str, destination: str, priority: Optional[int] = None):
		self._record_id: Optinal[int] = record_id
		self._record_type: str = record_type
		self._hostname:str = hostname
		self._destination: str = destination
		self._priority: Optinal[int] = priority
		self._delete: bool = False

	@classmethod
	def new(cls, record_type: str, hostname: str, destination:str, priority: Optional[int] = None) -> TDNSRecord:
		if record_type.upper() == "MX":
			if priority is None:
				priority = 10
		return cls(record_id = None, record_type = record_type, hostname = hostname, destination = destination, priority = priority)

	@property
	def record_id(self) -> Optional[int]:
		return self._record_id

	@property
	def record_type(self) -> str:
		return self._record_type

	@property
	def hostname(self) -> str:
		return self._hostname

	@property
	def destination(self) -> str:
		return self._destination

	@property
	def priority(self) -> Optional[int]:
		return self._priority

	@property
	def deleted(self) -> bool:
		return self._delete

	def _cmpkey(self):
		return (self.record_type, self.hostname, self.destination, self.priority)

	def delete(self):
		self._delete = True

	def dump(self, prefix = ""):
		components = [ ]
		if self.record_id is not None:
			components.append("[%10d]" % (self.record_id))
		else:
			components.append(" " * 12)
		components.append("%-4s %s -> %s" % (self.record_type.upper(), self.hostname, self.destination))
		if self.record_type.upper() == "MX":
			components.append("priority %d" % (self.priority))
		if self.deleted:
			components.append("<DELETE>")
		print(prefix + " ".join(components))

	@classmethod
	def deserialize(cls, data) -> TDNSRecord:
		if "priority" in data:
			priority = int(data["priority"])
			if priority == 0:
				priority = None
		else:
			priority = None
		record = cls(record_id = int(data["id"]), record_type = data["type"], hostname = data["hostname"], destination = data["destination"], priority = priority)
		if data.get("delete"):
			record.delete()
		return record

	def serialize(self) -> dict[str, Any]:
		if self.deleted and (self.record_id is None):
			# Delete entirely new record
			return None

		result = {
			"id":			self.record_id,
			"type":			self.record_type,
			"hostname":		self.hostname,
			"destination":	self.destination,
			"deleterecord":	self.deleted,
			"state":		None,
		}
		if self.priority is not None:
			result["priority"] = self.priority
		return result

	def __eq__(self, other):
		return isinstance(other, DNSRecord) and (self._cmpkey() == other._cmpkey())

	def __neq__(self, other):
		return not (self == other)

	def __hash__(self):
		return hash(self._cmpkey())

	def __repr__(self):
		return "DNSRecord<%s>" % (str(self._cmpkey()))

TDNSRecordSet = TypeVar("TDNSRecordSet", bound="DNSRecordSet")

class DNSRecordSet():
	def __init__(self, domainname):
		self._domainname: str = domainname
		self._records: list[TDNSRecord] = [ ]

	@property
	def domainname(self) -> str:
		return self._domainname

	@classmethod
	def from_recoTds(cls, domainname: str, dns_records: TDNSRecordSet) -> TDNSRecordSet:
		dns_record_set = cls(domainname)
		for dns_record in dns_records:
			dns_record_set.add(dns_record)
		return dns_record_set

	def delete_all(self):
		for record in self._records:
			record.delete()

	def delete_hostname(self, hostname: str):
		for record in self._records:
			if record.hostname == hostname:
				record.delete()

	def add(self, dns_record: TDNSRecord) -> TDNSRecordSet:
		assert(isinstance(dns_record, DNSRecord))
		self._records.append(dns_record)
		return self

	@classmethod
	def deserialize(cls, domainname: str, data: dict[str, Any]) -> TDNSRecordSet:
		assert(isinstance(data, dict))
		record_set = cls(domainname = domainname)
		for record_data in data["dnsrecords"]:
			record_set.add(DNSRecord.deserialize(record_data))
		return record_set

	def serialize(self) -> dict[str, TDNSRecordSet]:
		records = [ dns_record.serialize() for dns_record in self._records ]
		records = [ record for record in records if record is not None ]
		return { "dnsrecords": records }

	def __len__(self):
		return len(self._records)

	def __iter__(self):
		return iter(self._records)

	def dump(self):
		for (rec_no, record) in enumerate(self, 1):
			record.dump(prefix = "	%2d) " % (rec_no))

	def __str__(self):
		return "DNSRecordSet<%s: %d entries>" % (self.domainname, len(self))
