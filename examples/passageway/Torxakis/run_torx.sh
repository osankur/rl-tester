for i in {1..5000}
do
	echo "Trial $i"
	echo "run torx_script" | torxakis Passageway.txs

	output=`grep HIT /tmp/o`
	size=${#output}

	if [ $size -gt 0 ]; then 
		echo "HIT! See trace in /tmp/o" 
		exit 0
	fi

done
