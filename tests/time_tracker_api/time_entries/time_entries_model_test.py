from datetime import datetime, timedelta

import pytest
from faker import Faker

from commons.data_access_layer.cosmos_db import current_datetime, datetime_str
from time_tracker_api.time_entries.time_entries_model import TimeEntryCosmosDBRepository, TimeEntryCosmosDBModel

fake = Faker()

now = current_datetime()
yesterday = current_datetime() - timedelta(days=1)
two_days_ago = current_datetime() - timedelta(days=2)


def create_time_entry(start_date: datetime,
                      end_date: datetime,
                      owner_id: str,
                      tenant_id: str,
                      time_entry_repository: TimeEntryCosmosDBRepository) -> TimeEntryCosmosDBModel:
    data = {
        "project_id": fake.uuid4(),
        "activity_id": fake.uuid4(),
        "description": fake.paragraph(nb_sentences=2),
        "start_date": datetime_str(start_date),
        "end_date": datetime_str(end_date),
        "owner_id": owner_id,
        "tenant_id": tenant_id
    }

    created_item = time_entry_repository.create(data, mapper=TimeEntryCosmosDBModel)
    return created_item


@pytest.mark.parametrize(
    'start_date,end_date', [(two_days_ago, yesterday), (now, None)]
)
def test_find_interception_with_date_range_should_find(start_date: datetime,
                                                       end_date: datetime,
                                                       owner_id: str,
                                                       tenant_id: str,
                                                       time_entry_repository: TimeEntryCosmosDBRepository):
    existing_item = create_time_entry(start_date, end_date, owner_id, tenant_id, time_entry_repository)

    try:
        result = time_entry_repository.find_interception_with_date_range(datetime_str(yesterday), datetime_str(now),
                                                                         owner_id=owner_id,
                                                                         partition_key_value=tenant_id)

        assert result is not None
        assert len(result) >= 0
        assert any([existing_item.id == item.id for item in result])
    finally:
        time_entry_repository.delete_permanently(existing_item.id, partition_key_value=existing_item.tenant_id)


def test_find_interception_should_ignore_id_of_existing_item(owner_id: str,
                                                             tenant_id: str,
                                                             time_entry_repository: TimeEntryCosmosDBRepository):
    start_date = datetime_str(yesterday)
    end_date = datetime_str(now)
    existing_item = create_time_entry(yesterday, now, owner_id, tenant_id, time_entry_repository)
    try:

        colliding_result = time_entry_repository.find_interception_with_date_range(start_date, end_date,
                                                                                   owner_id=owner_id,
                                                                                   partition_key_value=tenant_id)

        non_colliding_result = time_entry_repository.find_interception_with_date_range(start_date, end_date,
                                                                                       owner_id=owner_id,
                                                                                       partition_key_value=tenant_id,
                                                                                       ignore_id=existing_item.id)

        colliding_result is not None
        assert any([existing_item.id == item.id for item in colliding_result])

        non_colliding_result is not None
        assert not any([existing_item.id == item.id for item in non_colliding_result])
    finally:
        time_entry_repository.delete_permanently(existing_item.id, partition_key_value=existing_item.tenant_id)


def test_find_running_should_return_running_time_entry(running_time_entry,
                                                       time_entry_repository: TimeEntryCosmosDBRepository):
   found_time_entry = time_entry_repository.find_running(partition_key_value=running_time_entry.tenant_id)

   assert found_time_entry is not None
   assert found_time_entry.id == running_time_entry.id


def test_find_running_should_not_find_any_item(tenant_id: str,
                                               time_entry_repository: TimeEntryCosmosDBRepository):
    try:
        time_entry_repository.find_running(partition_key_value=tenant_id)
    except Exception as e:
        assert type(e) is StopIteration
