from __future__ import absolute_import
from flask_login import login_user
from webserver.login import User
from webserver.testing import ServerTestCase
from db.testing import TEST_DATA_PATH
import db.exceptions
import webserver.views.api.exceptions
import webserver.views.api.v1.datasets
from utils import dataset_validator

import json
import mock
import os
import uuid


class APIDatasetViewsTestCase(ServerTestCase):

    def setUp(self):
        super(APIDatasetViewsTestCase, self).setUp()

        self.test_user_mb_name = "tester"
        self.test_user_id = db.user.create(self.test_user_mb_name)
        self.test_user = db.user.get(self.test_user_id)

        # Repeated values used for testing, TODO: use them in other tests
        self.dummy_json = json.dumps({"a": "thing"})
        self.dummy_str = "dummy string"
        self.dummy_uuid = "6b6b9205-f9c8-4674-92f5-2ae17bcb3cb0"

    def test_create_dataset_forbidden(self):
        """ Not logged in. """
        resp = self.client.post("/api/v1/datasets/")
        self.assertEqual(resp.status_code, 401)


    def test_create_dataset_no_data(self):
        """ No data or bad data POSTed. """
        self.temporary_login(self.test_user_id)

        resp = self.client.post("/api/v1/datasets/")
        self.assertEqual(resp.status_code, 400)
        expected = {"message": "Data must be submitted in JSON format."}
        self.assertEqual(resp.json, expected)

        resp = self.client.post("/api/v1/datasets/", data="test-not-json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json, expected)


    @mock.patch("db.dataset.create_from_dict")
    def test_create_dataset_validation_error(self, create_from_dict):
        """ return an error if create_from_dict returns a validation error """
        self.temporary_login(self.test_user_id)

        exception_error = "data is not valid"
        create_from_dict.side_effect = dataset_validator.ValidationException(exception_error)
        submit = json.dumps({"a": "thing"})
        resp = self.client.post("/api/v1/datasets/", data=submit, content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        expected = {"message": exception_error}
        self.assertEqual(resp.json, expected)


    @mock.patch("db.dataset.create_from_dict")
    def test_create_dataset_fields_added(self, create_from_dict):
        """ Fields are added to the dict before validation if they don't exist. """
        self.temporary_login(self.test_user_id)

        exception_error = "data is not valid"
        create_from_dict.side_effect = dataset_validator.ValidationException(exception_error)
        submit = json.dumps({"a": "thing"})
        resp = self.client.post("/api/v1/datasets/", data=submit, content_type='application/json')
        self.assertEqual(resp.status_code, 400)
        # The `public` and `classes` fields are added
        create_from_dict.assert_called_once_with({"a": "thing", "public": True, "classes": []}, self.test_user["id"])


    @mock.patch("db.dataset.create_from_dict")
    def test_create_dataset(self, create_from_dict):
        """ Successfully creates dataset. """
        self.temporary_login(self.test_user_id)
        create_from_dict.return_value = "6b6b9205-f9c8-4674-92f5-2ae17bcb3cb0"
        # Json format doesn't matter as we mock the create response
        submit = json.dumps({"a": "thing"})
        resp = self.client.post("/api/v1/datasets/", data=submit, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        expected = {"success": True, "dataset_id": "6b6b9205-f9c8-4674-92f5-2ae17bcb3cb0"}
        self.assertEqual(resp.json, expected)

    @mock.patch("db.dataset.get")
    def test_get_check_dataset_not_exists(self, get):
        # Dataset doesn't exist
        get.side_effect = db.exceptions.NoDataFoundException()
        with self.assertRaises(webserver.views.api.exceptions.APINotFound):
            webserver.views.api.v1.datasets.get_check_dataset("6b6b9205-f9c8-4674-92f5-2ae17bcb3cb0")
        get.assert_called_once_with("6b6b9205-f9c8-4674-92f5-2ae17bcb3cb0")

    @mock.patch("db.dataset.get")
    def test_get_check_dataset_public(self, get):
        # You can access a public dataset
        dataset = {"test": "dataset", "public": True}
        get.return_value = dataset

        res = webserver.views.api.v1.datasets.get_check_dataset("6b6b9205-f9c8-4674-92f5-2ae17bcb3cb0")
        self.assertEqual(res, dataset)
        get.assert_called_once_with("6b6b9205-f9c8-4674-92f5-2ae17bcb3cb0")

    @mock.patch("db.dataset.get")
    def test_get_check_dataset_yours(self, get):
        # You can access your private dataset
        login_user(User.from_dbrow(self.test_user))
        dataset = {"test": "dataset", "public": False, "author": self.test_user_id}
        get.return_value = dataset

        res = webserver.views.api.v1.datasets.get_check_dataset("6b6b9205-f9c8-4674-92f5-2ae17bcb3cb0")
        self.assertEqual(res, dataset)
        get.assert_called_once_with("6b6b9205-f9c8-4674-92f5-2ae17bcb3cb0")

    @mock.patch("db.dataset.get")
    def test_get_check_dataset_private(self, get):
        # You can't access someone else's private dataset

        login_user(User.from_dbrow(self.test_user))
        # Dataset with a different author to the logged in user
        dataset = {"test": "dataset", "public": False, "author": (self.test_user_id+1)}
        get.return_value = dataset

        with self.assertRaises(webserver.views.api.exceptions.APINotFound):
            webserver.views.api.v1.datasets.get_check_dataset("6b6b9205-f9c8-4674-92f5-2ae17bcb3cb0")
        get.assert_called_once_with("6b6b9205-f9c8-4674-92f5-2ae17bcb3cb0")

    def _execute_records_api(self, api_method):
        # Helper method for executing API url
        self.temporary_login(self.test_user_id)
        return api_method("/api/v1/datasets/{}/recordings".format(self.dummy_uuid),
                          data=self.dummy_json, content_type='application/json')

    def _test_method_records_api_error(self, mock_method, api_method, exception_class, api_code):
        # Wrapper for testing for records API errors
        exception_error = "exception_error"
        mock_method.side_effect = exception_class(exception_error)

        resp = self._execute_records_api(api_method)

        self.assertEqual(resp.status_code, api_code)
        expected = {"message": exception_error}
        self.assertEqual(resp.json, expected)

    def _test_method_records_success(self, api_method):
        # Wrapper for testing for successive API execution
        resp = self._execute_records_api(api_method)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json["success"], True)

    @mock.patch("db.dataset.add_recordings")
    def test_add_records_validation_error(self, add_recordings):
        """ Invalid JSON in PUT recordings """
        self._test_method_records_api_error(
            add_recordings, self.client.put, dataset_validator.ValidationException, 400)

    @mock.patch("db.dataset.add_recordings")
    def test_add_records_not_found_error(self, add_recordings):
        """ Non-existent class name in PUT recordings """
        self._test_method_records_api_error(
            add_recordings, self.client.put, db.exceptions.NoDataFoundException, 404)

    @mock.patch("db.dataset.add_recordings")
    def test_add_records(self, add_recordings):
        """ Successively PUT recordings """
        add_recordings.return_value = None
        self._test_method_records_success(self.client.put)

    @mock.patch("db.dataset.remove_recordings")
    def test_remove_records_validation_error(self, remove_recordings):
        """ Invalid JSON in DELETE recordings """
        self._test_method_records_api_error(
            remove_recordings, self.client.delete, dataset_validator.ValidationException, 400)

    @mock.patch("db.dataset.remove_recordings")
    def test_remove_records_not_found_error(self, remove_recordings):
        """ Non-existent class name in DELETE recordings """
        self._test_method_records_api_error(
            remove_recordings, self.client.delete, db.exceptions.NoDataFoundException, 404)

    @mock.patch("db.dataset.remove_recordings")
    def test_remove_records(self, remove_recordings):
        """ Successively DELETE recordings """
        remove_recordings.return_value = None
        self._test_method_records_success(self.client.delete)
