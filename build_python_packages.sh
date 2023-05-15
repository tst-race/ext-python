set -x

# Extract packages
for PYTHON_PKG in *.whl
do
    unzip -o $PYTHON_PKG -d ./
done

for PYTHON_PKG in *.tar.gz
do
    tar -xzvf $PYTHON_PKG -C ./
done

# Bring unbuilt python sources to top-level folder
# These probably should be done by running some form of
# `python3 setup.py install`
cp -r ./PyYAML-*/lib3/yaml .
cp -r ./pycryptodome-*/lib/Crypto .
cp -r ./threadloop-*/threadloop .
cp -r ./thrift-*/src ./thrift
cp -r ./tornado-*/tornado .
cp -r ./simplejson-*/simplejson .
cp -r ./jaeger-client-*/jaeger_client .
cp -r ./opentracing-*/opentracing .
cp -r ./pyimgur-*/pyimgur .
cp -r ./cffi-*/cffi .
cp -r ./future-*/src/future .

# Build C extensions

## pycryptodome
pushd ./pycryptodome-*/
rm -rf build/*
python3 setup.py build_ext \
    --library-dirs=$ANDROID_LIBRARY_DIRS \
    --include-dirs=$ANDROID_INCLUDE_DIRS

# rename *.cpython-37m-x86_64-linux-gnu.so files to just *.cpython-37m.so
find build/lib.*/Crypto -name "*.so" -exec bash -c 'mv $0 ${0/cpython-37m-*/cpython-37m.so}' {} \;
cp -r build/lib.*/Crypto ../
popd

## cffi
pushd ./cffi-*/
rm -rf build/*
python3 setup.py build_ext \
    --library-dirs=$ANDROID_LIBRARY_DIRS \
    --include-dirs=$ANDROID_INCLUDE_DIRS

# rename *.cpython-37m-x86_64-linux-gnu.so files to just *.cpython-37m.so
find build/lib.*/ -name "*.so" -exec bash -c 'mv $0 ${0/cpython-37m-*/cpython-37m.so}' {} \;
cp build/lib.*/_cffi_backend.cpython-37m.so ../
