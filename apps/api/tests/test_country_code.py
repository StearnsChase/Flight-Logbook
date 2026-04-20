import pytest
from myflightbook_api.models.country_code import CountryCodePrefix, HyphenPreference

def test_best_match_country_code():
    us_code = CountryCodePrefix(country_name="United States", prefix="N", hyphen_pref=HyphenPreference.NO_HYPHEN)
    ca_code = CountryCodePrefix(country_name="Canada", prefix="C", hyphen_pref=HyphenPreference.HYPHENATE)
    fr_code = CountryCodePrefix(country_name="France", prefix="F", hyphen_pref=HyphenPreference.HYPHENATE)
    all_codes = [us_code, ca_code, fr_code]
    
    assert CountryCodePrefix.best_match_country_code("N12345", all_codes).prefix == "N"
    assert CountryCodePrefix.best_match_country_code("C-FABC", all_codes).prefix == "C"
    assert CountryCodePrefix.best_match_country_code("F-ABCD", all_codes).prefix == "F"
    assert CountryCodePrefix.best_match_country_code("SIM123", all_codes).is_sim is True

def test_set_country_code_for_tail():
    us_code = CountryCodePrefix(country_name="United States", prefix="N", hyphen_pref=HyphenPreference.NO_HYPHEN)
    ca_code = CountryCodePrefix(country_name="Canada", prefix="C", hyphen_pref=HyphenPreference.HYPHENATE)
    all_codes = [us_code, ca_code]
    
    # Change N12345 to Canada
    new_tail = CountryCodePrefix.set_country_code_for_tail(ca_code, "N12345", 10, all_codes)
    assert new_tail == "C-12345"
    
    # Change C-FABC to US
    new_tail2 = CountryCodePrefix.set_country_code_for_tail(us_code, "C-FABC", 10, all_codes)
    # The suffix for Canada in this case is 'FABC'
    assert new_tail2 == "NFABC"
