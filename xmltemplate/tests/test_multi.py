import os
import unittest as test

from mongoengine import connect
from xmltemplate import models
from xmltemplate import schema

datadir = os.path.join(os.path.dirname(__file__), "data")


def setUpMongo():

    MONGO_USER = "myUserAdmin"
    MONGO_PASSWORD = "abc123"
    DB_NAME = "testdb"
    DB_SERVER = "localhost"
    MONGODB_URI = "mongodb://" + MONGO_USER + ":" + MONGO_PASSWORD + "@" + DB_SERVER + "/" + DB_NAME +"?authSource=admin"
    return connect(DB_NAME, host=MONGODB_URI)

def tearDownMongo(mc):
    try:
        db = mc.get_default_database()
        mc.drop_database(db.name)
    except Exception as  ex:
        pass


class TestMultiSchemas(test.TestCase):

    def setUp(self):
        self.mc = setUpMongo()

    def tearDown(self):
        tearDownMongo(self.mc)
        self.mc.close()
        self.mc = None

    def load_multi(self):
        pass

    def test_find_includers(self):
        schemafile = "experiments.xsd"
        schemapath = os.path.join(datadir, schemafile)
        schema.SchemaLoader.load_from_file(schemapath, schemafile, schemafile)

        schemafile = "microscopy-incl.xsd"
        schemapath = os.path.join(datadir, schemafile)
        # pdb.set_trace()
        schema.SchemaLoader.load_from_file(schemapath, schemafile)

        exp = models.Schema.get_by_name("experiments.xsd")
        self.assertEquals(exp.find_including_schema_names(),
                          ['microscopy-incl.xsd'])

    def test_recognize_location(self):
        schemafile = "experiments.xsd"
        schemapath = os.path.join(datadir, schemafile)
        schema.SchemaLoader.load_from_file(schemapath, schemafile)

        schemafile = "microscopy-incl.xsd"
        schemapath = os.path.join(datadir, schemafile)
        # pdb.set_trace()

        # location doesn't match
        with self.assertRaises(schema.FixableErrorsRemain):
            schema.SchemaLoader.load_from_file(schemapath, schemafile)

        loader = schema.SchemaLoader.from_file(schemapath, schemafile)
        loader.recognize_location("experiments.xsd", "experiments.xsd")
        loader.load()

        exp = models.Schema.get_by_name("experiments.xsd")
        self.assertEquals(exp.find_including_schema_names(),
                          ['microscopy-incl.xsd'])

    def test_find_importers(self):
        schemafile = "experiments.xsd"
        schemapath = os.path.join(datadir, schemafile)
        schema.SchemaLoader.load_from_file(schemapath, schemafile, schemafile)

        schemafile = "microscopy.xsd"
        schemapath = os.path.join(datadir, schemafile)
        # pdb.set_trace()
        schema.SchemaLoader.load_from_file(schemapath, schemafile)

        exp = models.Schema.get_by_name("experiments.xsd")
        self.assertEquals(exp.find_importing_schema_names(),
                          ['microscopy.xsd'])

    def test_recognize_ns(self):
        schemafile = "experiments.xsd"
        schemapath = os.path.join(datadir, schemafile)
        schema.SchemaLoader.load_from_file(schemapath, schemafile)

        # load again with a different name
        schemafile = "experiments.xsd"
        schemapath = os.path.join(datadir, schemafile)
        schema.SchemaLoader.load_from_file(schemapath, "experiments")

        schemafile = "microscopy.xsd"
        schemapath = os.path.join(datadir, schemafile)

        # location doesn't match
        with self.assertRaises(schema.FixableErrorsRemain):
            schema.SchemaLoader.load_from_file(schemapath, schemafile)

        loader = schema.SchemaLoader.from_file(schemapath, schemafile)
        loader.recognize_namespace("urn:experiments", "experiments.xsd")
        loader.load()

        exp = models.Schema.get_by_name("experiments.xsd")
        self.assertEquals(exp.find_importing_schema_names(),
                          ['microscopy.xsd'])

    def test_tri_import(self):
        resmddir = os.path.join(datadir, "resmd")

        schemafile = "xml-2001.xsd"
        schemapath = os.path.join(resmddir, schemafile)
        schema.SchemaLoader.load_from_file(schemapath, schemafile,
                                           "http://www.w3.org/2009/01/xml.xsd")

        schemafile = "res-md.xsd"
        schemapath = os.path.join(resmddir, schemafile)
        schema.SchemaLoader.load_from_file(schemapath, schemafile, schemafile)

        schemafile = "res-app.xsd"
        schemapath = os.path.join(resmddir, schemafile)
        # pdb.set_trace()
        schema.SchemaLoader.load_from_file(schemapath, schemafile, schemafile)

        resmd = models.Schema.get_by_name("res-md.xsd")
        self.assertEquals(resmd.find_importing_schema_names(),
                          ['res-app.xsd'])

        xmlxsd = models.Schema.get_by_name("xml-2001.xsd")
        importers = xmlxsd.find_importing_schema_names()
        self.assertIn('res-app.xsd', importers)
        self.assertIn('res-md.xsd', importers)

    def test_netimport(self):
        # test loading an imported schema from the internet
        resmddir = os.path.join(datadir, "resmd")

        # res-md.xsd will cause http://www.w3.org/2009/01/xml.xsd to be
        # automatically loaded from the internet
        schemafile = "res-md.xsd"
        schemapath = os.path.join(resmddir, schemafile)
        # pdb.set_trace()
        schema.SchemaLoader.load_from_file(schemapath, schemafile, schemafile)

    def test_full_import(self):
        resmddir = os.path.join(datadir, "resmd")
        self.test_tri_import()

        schemafile = "resmd-datacite.xsd"
        schemapath = os.path.join(resmddir, schemafile)
        schema.SchemaLoader.load_from_file(schemapath, schemafile, schemafile)

        schemafile = "resmd-access.xsd"
        schemapath = os.path.join(resmddir, schemafile)
        schema.SchemaLoader.load_from_file(schemapath, schemafile, schemafile)

        schemafile = "mat-sci_res-md.xsd"
        schemapath = os.path.join(resmddir, schemafile)
        schema.SchemaLoader.load_from_file(schemapath, schemafile, schemafile)

        # find importers
        xmlxsd = models.Schema.get_by_name("res-md.xsd")
        importers = xmlxsd.find_importing_schema_names()
        self.assertIn('res-app.xsd', importers)
        self.assertIn('resmd-access.xsd', importers)
        self.assertIn('resmd-datacite.xsd', importers)

        # check subtypes
        resmd_ns = "http://schema.nist.gov/xml/res-md/1.0wd"
        acces_ns = "http://schema.nist.gov/xml/resmd-access/1.0wd"
        access_q = "{http://schema.nist.gov/xml/resmd-access/1.0wd}"
        res = models.GlobalType.objects.filter(namespace=resmd_ns) \
            .get(name='Resource')
        subtps = res.list_subtypes(False)
        self.assertEquals(len(subtps), 1)
        self.assertEquals(subtps[0], access_q + "AccessibleResource")

        role = models.GlobalType.objects.filter(namespace=resmd_ns) \
            .get(name='Role')
        subtps = role.list_subtypes(False)
        self.assertEquals(len(subtps), 2)
        self.assertIn(access_q + "Software", subtps)
        self.assertIn(access_q + "ServiceAPI", subtps)

        role = models.GlobalType.objects.filter(namespace=resmd_ns) \
            .get(name='Role')
        subtps = role.list_subtypes(True)
        self.assertEquals(len(subtps), 4)
        self.assertIn(access_q + "SoftwareRoleTypeRestriction", subtps)
        self.assertIn(access_q + "Software", subtps)
        self.assertIn(access_q + "ServiceAPIRoleTypeRestriction", subtps)
        self.assertIn(access_q + "ServiceAPI", subtps)


# TODO:  check loading of types, tracking of ancestors
#        review when types are incomplete; handle ambiguities
#        support finding all subtypes (abstract?)
#        test templates


TESTS = ["TestMultiSchemas"]


def test_suite():
    suite = test.TestSuite()
    suite.addTests([test.makeSuite(TestMultiSchemas)])
    return suite


if __name__ == '__main__':
    test.main()
