set -e
sudo apt update
sudo apt install git iverilog gtkwave yosys berkeley-abc
pip3 install dd py-aiger graphviz

git clone -b reach_synth git@gitlab.inria.fr:osankur/abssynthe
cd abssynthe
./build.sh
echo "export PATH=\$PATH:`pwd`/binary/" >> ~/.bashrc
cd ..

# Aiger
git clone https://github.com/osankur/aiger
cd aiger
chmod +x configure.sh
./configure.sh && make
make
echo "export PATH=\$PATH:`pwd`" >> ~/.bashrc

cd ../scripts
make
source ~/.bashrc
