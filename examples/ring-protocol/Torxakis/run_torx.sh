for i in {1..1000}
do
	echo "Trial $i"
	echo "run torx_script" | torxakis Ring.txs

	output=`grep Hit /tmp/o`
	size=${#output}

	if [ $size -gt 0 ]; then 
		echo "HIT! See trace in /tmp/o" 
		exit 0
	fi

done
