# importing pyspatialite
from pyspatialite import dbapi2 as db

# creating/connecting the test_db
conn = db.connect('test_db.sqlite')

# creating a Cursor
cur = conn.cursor()

# testing library versions
rs = cur.execute('SELECT sqlite_version(), spatialite_version()')
for row in rs:
    msg = "> SQLite v%s Spatialite v%s" % (row[0], row[1])
    print msg

# initializing Spatial MetaData
# using v.2.4.0 this will automatically create
# GEOMETRY_COLUMNS and SPATIAL_REF_SYS
sql = 'SELECT InitSpatialMetadata()'
cur.execute(sql)

# creating a POLYGON table
sql = 'CREATE TABLE test_pg ('
sql += 'id INTEGER NOT NULL PRIMARY KEY,'
sql += 'name TEXT NOT NULL)'
cur.execute(sql)
# creating a POLYGON Geometry column
sql = "SELECT AddGeometryColumn('test_pg', "
sql += "'geom', 4326, 'POLYGON', 'XY')"
cur.execute(sql)

# inserting some POLYGONs
for i in range(10):
    name = "test POLYGON #%d" % (i+1)
    geom = "GeomFromText('POLYGON(("
    geom += "%f " % (-10.0 - (i / 1000.0))
    geom += "%f, " % (-10.0 - (i / 1000.0))
    geom += "%f " % (10.0 + (i / 1000.0))
    geom += "%f, " % (-10.0 - (i / 1000.0))
    geom += "%f " % (10.0 + (i / 1000.0))
    geom += "%f, " % (10.0 + (i / 1000.0))
    geom += "%f " % (-10.0 - (i / 1000.0))
    geom += "%f, " % (10.0 + (i / 1000.0))
    geom += "%f " % (-10.0 - (i / 1000.0))
    geom += "%f" % (-10.0 - (i / 1000.0))
    geom += "))', 4326)"
    sql = "INSERT INTO test_pg (id, name, geom) "
    sql += "VALUES (%d, '%s', %s)" % (i+1, name, geom)
    cur.execute(sql)
conn.commit()

# checking POLYGONs
sql = "SELECT DISTINCT Count(*), ST_GeometryType(geom), "
sql += "ST_Srid(geom) FROM test_pg"
rs = cur.execute(sql)
for row in rs:
    msg = "> Inserted %d entities of type " % (row[0])
    msg += "%s SRID=%d" % (row[1], row[2])
    print msg

rs.close()
conn.close()
quit()