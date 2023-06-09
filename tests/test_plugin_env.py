import logging
from string import ascii_letters, digits

import pytest
from hypothesis import given, example, settings, Verbosity
from hypothesis import strategies as st
from faker import Faker

import polyconf.core.model.context
import polyconf.core.model.datum
import polyconf.core.model.status
from polyconf.core import model
from polyconf.core.utils import pipe
from polyconf.plugins.env import plugin


logger = logging.getLogger(__name__)
fake = Faker()


import os
from contextlib import contextmanager


@contextmanager
def environ(**env):
    """https://gist.github.com/igniteflow/7267431?permalink_comment_id=4314590#gistcomment-4314590"""
    originals = {k: os.environ.get(k) for k in env}
    for k, val in env.items():
        if val is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = val
    try:
        yield
    finally:
        for k, val in originals.items():
            if val is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = val


@pytest.fixture
def env_plugin():
    return plugin.factory(logger=logger)


@pytest.fixture
def _mock_acme_env(monkeypatch):
    monkeypatch.setenv("ACME_LOREM", "lorem")
    monkeypatch.setenv("ACME_IPSUM", "ipsum")


@pytest.fixture
def _mock_acme_env_nested(monkeypatch):
    monkeypatch.setenv("ACME_LOREM__DOLAR__AMET", "lorem")
    monkeypatch.setenv("ACME_IPSUM__DOLAR__AMET", "ipsum")


@pytest.fixture
def context():
    return polyconf.core.model.context.Context(
        app_name="acme",
        app_prefix="ACME",
        trim_prefix=True,
    )


def test_fake(env_plugin, context, _mock_acme_env_nested):
    result = env_plugin.hydrate(context)

    assert result.status != polyconf.core.model.status.Status.NEW
    assert result.status == polyconf.core.model.status.Status.OK

    # assert result.result == model.Datum(
    #     name="root",
    #     value=None,
    #     children={
    #         model.Datum(name="LOREM", value="lorem", children=set(), sources={"env://LOREM"}),
    #         model.Datum(name="IPSUM", value="ipsum", children=set(), sources={"env://IPSUM"}),
    #     },
    #     sources=set(),
    # )
    assert result.result == polyconf.core.model.datum.Datum(
        name="root",
        value=None,
        children={
            polyconf.core.model.datum.Datum(
                name="IPSUM",
                value=None,
                children={
                    polyconf.core.model.datum.Datum(
                        name="DOLAR",
                        value=None,
                        children={polyconf.core.model.datum.Datum(name="AMET", value="ipsum", children=set(), sources={"env://IPSUM__DOLAR__AMET"})},
                        sources={"env://IPSUM__DOLAR__AMET"},
                    ),
                },
                sources={"env://IPSUM__DOLAR__AMET"},
            ),
            polyconf.core.model.datum.Datum(
                name="LOREM",
                value=None,
                children={
                    polyconf.core.model.datum.Datum(
                        name="DOLAR",
                        value=None,
                        children={polyconf.core.model.datum.Datum(name="AMET", value="lorem", children=set(), sources={"env://LOREM__DOLAR__AMET"})},
                        sources={"env://LOREM__DOLAR__AMET"},
                    ),
                },
                sources={"env://LOREM__DOLAR__AMET"},
            ),
        },
        sources=set(),
    )


@given(app_name=st.text(min_size=1, alphabet=ascii_letters + digits))
def test_fake2(app_name):
    simple_u = fake.word().upper()
    simple_l = simple_u.lower()
    lvl1_u = fake.word().upper()
    lvl1_l = lvl1_u.lower()
    lvl2_u = fake.word().upper()
    lvl2_l = lvl2_u.lower()
    env_plugin = plugin.factory(logger=logger)
    # monkeypatch.setenv(f"{app_name.upper()}_LOREM", "lorem")
    # monkeypatch.setenv(f"{app_name.upper()}_IPSUM", "ipsum")
    ctx = polyconf.core.model.context.Context(
        app_name=app_name,
        # app_prefix="ACME",
        trim_prefix=True,
    )

    new_env_vars = {
        f"{app_name.upper()}_{simple_u}": simple_l,
        f"{app_name.upper()}_{lvl1_u}__{lvl2_u}": lvl2_l,
    }
    with environ(**new_env_vars):
        result = env_plugin.hydrate(ctx)

    assert result.status != polyconf.core.model.status.Status.NEW
    assert result.status == polyconf.core.model.status.Status.OK

    assert result.as_obj[simple_u] == simple_l
    assert result.as_obj[f"{lvl1_u}__{lvl2_u}"] == lvl2_l
    assert len(result.as_obj) == 2
    # assert result.as_obj == {
    #     simple_u: simple_l,
    #     # f"{lvl1_u}__{lvl2_u}": lvl2_l,  # <-- current result (bad)
    #     lvl1_u: {  # <-- desired result
    #         lvl2_u: lvl2_l
    #     }
    # }

    # TODO: THOUGHTS: When expecting nested data, it should not be possible to specify
    #       both nested values and a static value for the container itself.
    #           # This is not valid!
    #           FOO = "x"
    #           FOO__BAR = "y"
    #           FOO__BAZ = "z"
    #           # A valid case is if the top "x" wasn't there, then the result would be:
    #           result = {
    #               "FOO": {
    #                   "BAR": "y",
    #                   "BAZ": "z",
    #               },
    #           }
    #       Conflict with the SAME source should raise an error.
    #       Conflict with a PREVIOUS source _should_ be covered by normal behavior
    #           otherwise favor nested over static.
