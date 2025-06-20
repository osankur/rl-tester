for i in {1..5000}
do
	echo "Trial $i"
	echo "run torx_script" | torxakis Ring.txs

	output=`grep Hit /tmp/o`
	size=${#output}

	echo $output
	exit 0
	if [ $size -gt 0 ]; then 
		echo "HIT! See trace in /tmp/o" 
		exit 0
	fi

done
