LLVM_VER=3.5.0

define fetch-and-unpack
rm -rf $(2)
mkdir $(2)
curl http://releases.llvm.org/$(LLVM_VER)/$(1)-$(LLVM_VER).src.tar.xz | tar --extract --xz --file=- --strip-components=1 --directory=$(2)
endef


all: install

install: src
	rm -rf build
	mkdir build
	( \
	  cd build && \
	  ../src/configure CXXFLAGS=-fno-devirtualize LDFLAGS=-Wl,-rpath,/s/gcc-4.9.2/lib --prefix="`pwd`/../install" --enable-cxx11 --enable-shared && \
	  make -j"`nproc`" REQUIRES_RTTI=1 && \
	  make install \
	)

src: template-friend-fix.patch
	$(call fetch-and-unpack,llvm,$@)
	$(call fetch-and-unpack,cfe,$@/tools/clang)
	$(call fetch-and-unpack,compiler-rt,$@/projects/compiler-rt)
	patch --strip=0 <$<

clean:
	rm -rf src build install
