import logging
from flask import flash, redirect, url_for, Blueprint, request
from redash.authentication import create_and_login_user, logout_and_redirect_to_index
from redash.authentication.org_resolving import current_org
from redash.handlers.base import org_scoped_rule
from saml2 import BINDING_HTTP_POST, BINDING_HTTP_REDIRECT, entity
from saml2.client import Saml2Client
from saml2.config import Config as Saml2Config
from saml2.saml import NAMEID_FORMAT_TRANSIENT
from saml2.mdstore import MetaDataExtern
try:
    from urllib.parse import urlparse
except ImportError:
     from urlparse import urlparse
     from urlparse import urlunparse
import os
logger = logging.getLogger('saml_auth')
blueprint = Blueprint('saml_auth', __name__)
def get_saml_client(org):
    """
    Return SAML configuration.
    The configuration is a hash for use by saml2.config.Config
    """
    metadata_url = org.get_setting("auth_saml_metadata_url")
    entity_id = org.get_setting("auth_saml_entity_id")
    acs_url = url_for("saml_auth.idp_initiated", org_slug=org.slug, _external=True)
    saml_settings = {
        'metadata': {
            "remote": [{
                "url": metadata_url
            }]
        },
        'service': {
            'sp': {
                'endpoints': {
                    'assertion_consumer_service': [
                        (acs_url, BINDING_HTTP_REDIRECT),
                        (acs_url, BINDING_HTTP_POST)
                    ],
                },
                # Don't verify that the incoming requests originate from us via
                # the built-in cache for authn request ids in pysaml2
                'allow_unsolicited': True,
                # Don't sign authn requests, since signed requests only make
                # sense in a situation where you control both the SP and IdP
                'authn_requests_signed': False,
                'logout_requests_signed': True,
                'want_assertions_signed': True,
                'want_response_signed': False,
            },
        },
    }
    if entity_id is not None and entity_id != "":
        saml_settings['entityid'] = entity_id
    sp_config = Saml2Config()
    sp_config.load(saml_settings)
    sp_config.allow_unknown_attributes = True
    saml_client = Saml2Client(config=sp_config)
    return saml_client
@blueprint.route(org_scoped_rule('/saml/callback'), methods=['POST'])
def idp_initiated(org_slug=None):
    if not current_org.get_setting("auth_saml_enabled"):
        logger.error("SAML Login is not enabled")
        return redirect(url_for('redash.index', org_slug=org_slug))
    saml_client = get_saml_client(current_org)
    saml_client_urls_upgrade(saml_client)
    try:
        authn_response = saml_client.parse_authn_request_response(
            request.form['SAMLResponse'],
            entity.BINDING_HTTP_POST)
    except Exception:
        logger.error('Failed to parse SAML response', exc_info=True)
        flash('SAML login failed. Please try again later.')
        return redirect(url_for('redash.login', org_slug=org_slug))
    authn_response.get_identity()
    user_info = authn_response.get_subject()
    email = user_info.text
    try:
        name = "%s %s" % (authn_response.ava['FirstName'][0], authn_response.ava['LastName'][0])
    except Exception as e:
        name = email.split('@')[0]
    # This is what as known as "Just In Time (JIT) provisioning".
    # What that means is that, if a user in a SAML assertion
    # isn't in the user store, we create that user first, then log them in
    user = create_and_login_user(current_org, name, email)
    if user is None:
        return logout_and_redirect_to_index()
    if 'RedashGroups' in authn_response.ava:
        group_names = authn_response.ava.get('RedashGroups')
        user.update_group_assignments(group_names)
    url = url_for('redash.index', org_slug=org_slug)
    return redirect(url)
@blueprint.route(org_scoped_rule("/saml/login"))
def sp_initiated(org_slug=None):
    if not current_org.get_setting("auth_saml_enabled"):
        logger.error("SAML Login is not enabled")
        return redirect(url_for('redash.index', org_slug=org_slug))
    saml_client = get_saml_client(current_org)
    nameid_format = current_org.get_setting('auth_saml_nameid_format')
    if nameid_format is None or nameid_format == "":
        nameid_format = NAMEID_FORMAT_TRANSIENT
    saml_client_urls_upgrade(saml_client)
    _, info = saml_client.prepare_for_authenticate(nameid_format=nameid_format)
    redirect_url = None
    # Select the IdP URL to send the AuthN request to
    for key, value in info['headers']:
        if key == 'Location':
            redirect_url = value
    response = redirect(redirect_url, code=302)
    # NOTE:
    #   I realize I _technically_ don't need to set Cache-Control or Pragma:
    #     https://stackoverflow.com/a/5494469
    #   However, Section 3.2.3.2 of the SAML spec suggests they are set:
    #     http://docs.oasis-open.org/security/saml/v2.0/saml-bindings-2.0-os.pdf
    #   We set those headers here as a "belt and suspenders" approach,
    #   since enterprise environments don't always conform to RFCs
    response.headers['Cache-Control'] = 'no-cache, no-store'
    response.headers['Pragma'] = 'no-cache'
    return response
def saml_client_urls_upgrade(saml_client):
    saml_redirect_url = os.getenv('REDASH_SAML_REDIRECT_URL')
    if saml_redirect_url:
        eids = saml_client.metadata.with_descriptor("idpsso")
        default_netloc = urlparse(list(eids.keys())[0])
        new_netloc = urlparse(saml_redirect_url)
        keys_replacer(saml_client.metadata.metadata, default_netloc, new_netloc)
        location_replacer(saml_client.metadata.metadata, default_netloc, new_netloc)
        keys_replacer(eids, default_netloc, new_netloc)
        location_replacer(eids, default_netloc, new_netloc)
def keys_replacer(storage, default_netloc, new_netloc):
    new_keys = {}
    delete_keys = []
    for k, v in m_enum(storage):
        if type(k) is str and default_netloc.netloc in k:
            new_k = location_replace(k, default_netloc, new_netloc)
            new_keys[new_k] = v
            delete_keys.append(k)
        if type(v) is dict or type(v) is list or isinstance(v, MetaDataExtern):
            keys_replacer(v, default_netloc, new_netloc)
            storage[k] = v
    for k in delete_keys:
        del storage[k]
    for k, v in new_keys.items():
        storage[k] = v
def location_replacer(storage, default_netloc, new_netloc):
    if storage is None:
        return storage
    for k, v in m_enum(storage):
        if k == 'location':
            storage[k] = location_replace(v, default_netloc, new_netloc)
            continue
        if type(v) is dict or type(v) is list:
            location_replacer(v, default_netloc, new_netloc)
            storage[k] = v
    return storage
def location_replace(location_url, default_netloc, new_netloc):
    location_parsed = urlparse(location_url)
    if location_parsed.netloc == default_netloc.netloc:
        return urlunparse(
            location_parsed._replace(netloc=new_netloc.netloc).
                _replace(scheme=new_netloc.scheme))
    return location_url
def m_enum(d):
    if type(d) is dict or isinstance(d, MetaDataExtern):
        return d.items()
    if type(d) is list:
        return enumerate(d)
    return d
