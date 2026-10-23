from logic import validate_fact,allowed_to_generate,review_result,fact_hash,news_prompt
def test_no_source():
 assert validate_fact({'value_text':'축제','source_id':3,'fact_type':'text'}, {})
def test_valid_source():
 assert not validate_fact({'value_text':'축제','source_id':3,'fact_type':'text'},{3:{'organization':'관광청','source_url':'https://example.org','published_at':'2026-10-19'}})
def test_unverified_blocked():
 assert not allowed_to_generate([{'status':'candidate','source_id':3}])
def test_all_verified():
 assert allowed_to_generate([{'status':'verified','source_id':3}])
def test_review_failure():
 assert not review_result({'numbers':True,'time_and_region':True,'no_unfounded_causes':False,'source_and_observed_at':True})
def test_review_all_pass():
 assert review_result({'numbers':True,'time_and_region':True,'no_unfounded_causes':True,'source_and_observed_at':True})
def test_snapshot_changes():
 assert fact_hash([{'value_text':'A'}])!=fact_hash([{'value_text':'B'}])
def test_prompt_gate():
 import pytest
 with pytest.raises(ValueError):news_prompt('축제',[{'status':'candidate','source_id':3}])
