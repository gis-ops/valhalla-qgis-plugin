for f in valhalla/gui/*.ui
do
  file_base=$(basename "$f")
  py_f=${file_base%%.*}
  echo "compiled $py_f"
  pyuic5  $f > valhalla/gui/"${py_f}_ui.py"
done
