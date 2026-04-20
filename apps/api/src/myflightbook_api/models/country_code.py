from __future__ import annotations

import enum

from sqlalchemy import Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from myflightbook_api.db.base import Base


class RegistrationTemplateMode(enum.IntEnum):
    NO_SEARCH = 0
    WHOLE_TAIL = 1
    SUFFIX_ONLY = 2
    WHOLE_WITH_DASH = 3


class HyphenPreference(enum.IntEnum):
    NONE = 0
    HYPHENATE = 1
    NO_HYPHEN = 2


class CountryCodePrefix(Base):
    __tablename__ = "country_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    country_name: Mapped[str] = mapped_column(String(255))
    prefix: Mapped[str] = mapped_column(String(10))
    locale: Mapped[str | None] = mapped_column(String(5), nullable=True)
    registration_url_template: Mapped[str | None] = mapped_column(String(255), nullable=True)
    template_type: Mapped[RegistrationTemplateMode] = mapped_column(Enum(RegistrationTemplateMode), default=RegistrationTemplateMode.NO_SEARCH)
    hyphen_pref: Mapped[HyphenPreference] = mapped_column(Enum(HyphenPreference), default=HyphenPreference.NONE)

    SIM_PREFIX = "SIM"
    ANON_PREFIX = "#"

    @property
    def hyphenated_prefix(self) -> str:
        if self.hyphen_pref == HyphenPreference.HYPHENATE:
            return f"{self.prefix}-"
        return self.prefix

    @property
    def normalized_prefix(self) -> str:
        return self.prefix.replace("-", "") if self.prefix else ""

    @property
    def is_sim(self) -> bool:
        return self.prefix.upper() == self.SIM_PREFIX if self.prefix else False

    @property
    def is_anonymous(self) -> bool:
        return self.prefix.upper() == self.ANON_PREFIX if self.prefix else False

    @property
    def is_unknown(self) -> bool:
        return not self.prefix

    @classmethod
    def get_sim_country(cls) -> CountryCodePrefix:
        return cls(country_name="(Simulator)", prefix=cls.SIM_PREFIX)

    @classmethod
    def get_anonymous_country(cls) -> CountryCodePrefix:
        return cls(country_name="(Anonymous)", prefix=cls.ANON_PREFIX)

    @classmethod
    def get_unknown_country(cls) -> CountryCodePrefix:
        return cls(country_name="(Unknown)", prefix="")

    @classmethod
    def best_match_country_code(cls, tail: str, all_codes: list[CountryCodePrefix]) -> CountryCodePrefix:
        if not tail:
            raise ValueError("Tail number cannot be null or empty")

        if tail.upper().startswith(cls.SIM_PREFIX):
            return cls.get_sim_country()

        if tail.upper().startswith(cls.ANON_PREFIX):
            return cls.get_anonymous_country()

        best_match = cls.get_unknown_country()
        compare_tail = tail.replace("-", "")

        for code in all_codes:
            if compare_tail.upper().startswith(code.normalized_prefix.upper()) and len(code.normalized_prefix) > len(best_match.normalized_prefix):
                best_match = code

        return best_match

    @classmethod
    def set_country_code_for_tail(cls, new_code: CountryCodePrefix, tail: str, max_length: int, all_codes: list[CountryCodePrefix]) -> str:
        if not tail:
            return ""

        if tail.upper().startswith(cls.ANON_PREFIX) or tail.upper().startswith(cls.SIM_PREFIX):
            return tail

        old_code = cls.best_match_country_code(tail, all_codes)
        normalized_tail = tail.replace("-", "")
        
        new_tail = tail
        if old_code.prefix.upper() != new_code.prefix.upper():
            new_tail = new_code.hyphenated_prefix + normalized_tail[len(old_code.normalized_prefix):]
            if len(new_tail) > max_length:
                new_tail = new_tail[:max_length]
                
        return new_tail.upper()
