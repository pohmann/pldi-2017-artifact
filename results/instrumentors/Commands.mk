SCHEMAS_DIR := $(shell pwd)/../../csi-cc/schemas

INSTRUMENTORS := csi

all: $(INSTRUMENTORS)

$(INSTRUMENTORS): %: %.in
	sed -e 's|@SCHEMA_DIR@|$(SCHEMAS_DIR)|' $@.in >| $@
	chmod u+x $@

clean:
	-rm -f $(INSTRUMENTORS)
