.PHONY: package-deps package-build package-check package-upload package clean

package-deps:
	python3 -m pip install --upgrade build

package-build: package-deps
	python3 -m build

package-check: package-build     ## Check the distribution is valid
	python3 -m twine check dist/*

package-upload: package-deps package-check
	python3 -m twine upload dist/* --repository-url https://upload.pypi.org/legacy/

package: package-upload

clean:
	rm -rf brunnhilde.egg-info/
	rm -rf build/
	rm -rf dist/
