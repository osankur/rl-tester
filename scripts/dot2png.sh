for f in *.dot; do
	dot -Tpng $f > $f.png;
done
