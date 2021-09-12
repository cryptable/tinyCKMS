import logging

from cryptography import x509
from cryptography.x509 import oid
from cryptography.hazmat.primitives import hashes

from flask import current_app

from tinyCKMS.db import db


class SubjectAltName(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)
    value = db.Column(db.String(64), nullable=False)
    cert_id = db.Column(db.Integer, db.ForeignKey('certificate.id'), nullable=False)


class Certificate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject_cn = db.Column(db.String(64), nullable=False, index=True)
    subject_dn = db.Column(db.String(1024), nullable=False)
    issuer_dn = db.Column(db.String(1024), nullable=False)
    serial_nbr = db.Column(db.String(80), nullable=False)
    subject_alt_names = db.relation('SubjectAltName', backref='cert', lazy=True)
    cert = db.Column(db.Text, nullable=False, unique=True)
    sha256_thumbprint = db.Column(db.BINARY(32), nullable=False)
    not_valid_after = db.Column(db.DateTime, nullable=False, index=True)

    def __repr__(self):
        return '<Certificate %r:%r>' % (self.issuer_dn, self.serial_nbr)


def get_subject_alt_names(certificate):
    sans = certificate.extensions.get_extension_for_oid(oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
    if sans is None:
        return None
    result = []
    for general_name in sans.value._general_names:
        if isinstance(general_name, x509.DNSName):
            result.append(SubjectAltName(type='DNS', value=general_name.value))
        elif isinstance(general_name, x509.IPAddress):
            result.append(SubjectAltName(type='IP', value=str(general_name.value)))
        elif isinstance(general_name, x509.UniformResourceIdentifier):
            result.append(SubjectAltName(type='URI', value=general_name.value))
        elif isinstance(general_name, x509.DirectoryName):
            result.append(SubjectAltName(type='LDAP', value=general_name.value))
        elif isinstance(general_name, x509.RFC822Name):
            result.append(SubjectAltName(type='eMail', value=general_name.value))
        elif isinstance(general_name, x509.RegisteredID):
            result.append(SubjectAltName(type='RegisteredID', value=general_name.value))
        else:
            logging.warning(f"Unkown SAN type for {general_name}")
    return result


def add_certificate(pem_certificate):
    certificate = x509.load_pem_x509_certificate(pem_certificate.encode('utf-8'))
    cert_obj = Certificate(
        subject_cn=certificate.subject.get_attributes_for_oid(oid.NameOID.COMMON_NAME)[0].value,
        subject_dn=certificate.subject.rfc4514_string(),
        issuer_dn=certificate.issuer.rfc4514_string(),
        serial_nbr=hex(certificate.serial_number),
        subject_alt_names=get_subject_alt_names(certificate),
        cert=pem_certificate,
        sha256_thumbprint=certificate.fingerprint(hashes.SHA256()),
        not_valid_after=certificate.not_valid_after
    )
    with current_app.app_context():
        db.session.add(cert_obj)
        db.session.commit()
