const utils = {
  renameObjectKey(object, oldKey, newKey) {
    Object.defineProperty(object, newKey, Object.getOwnPropertyDescriptor(object, oldKey))
    delete object[oldKey]
    return object
  },
  isObjectsSimilar(object1, object2) {
    return Object.keys(object1).every(
            key => {
                if(key != 'id' && key != 'apiSource') return object2.hasOwnProperty(key) && object2[key] === object1[key]
                return true
            })
  },
  findSimilarObjectsKeyWithSameValues(object1,object2) {
    const similarKeysWithSameValues = []

    Object.keys(object1).map(key => {
      if (object2.hasOwnProperty(key) && this.isObjectsSimilar(object1[key], object2[key])) {
        similarKeysWithSameValues.push(key)
      }
      return key
    })
    return similarKeysWithSameValues
  },
  findSimilarObjectsKeyWithDifferentsValues(object1, object2) {
    const similarKeysWithDifferentsValues = []
    Object.keys(object1).map(key => {
      if (object2.hasOwnProperty(key) && object2[key].val !== object1[key].val) {
        similarKeysWithDifferentsValues.push(key)
      }
      return key
    })
    return similarKeysWithDifferentsValues
  },
    getKeyAlreadyDuplicated: (firstEntity, secondEntity) => {
    let keysAlreadyDuplicated = Object.keys(firstEntity).map(key => {
      const keySplitted = key.split('^')
      if (keySplitted.length > 1 && Number(keySplitted[1])) {
        const mappingDuplicateKeyToActualKey = {}
        mappingDuplicateKeyToActualKey[keySplitted[0]] = key
        return mappingDuplicateKeyToActualKey
      }
      else return null
    }).filter(key => key)
    Object.keys(secondEntity).map(keyFromSecondEntity => {
      const keyFromFirstEntity = keysAlreadyDuplicated.filter(key => key[keyFromSecondEntity])
      if (keyFromFirstEntity.length > 0) {
        if (keyFromFirstEntity.filter(
          key =>  firstEntity[key[keyFromSecondEntity]].val === secondEntity[keyFromSecondEntity].val
          ).length === 0) {
            secondEntity = utils.renameObjectKey(
              secondEntity,
              keyFromSecondEntity,
              `${keyFromSecondEntity}_${secondEntity[keyFromSecondEntity].apiSource}`
              )
          }
        else {
          delete secondEntity[keyFromSecondEntity]
        }
      }
      return  keyFromSecondEntity
    })
    return secondEntity
  },
  copyArrayOfArrayWithObject: arrayOfArrayWithObject => {
    const arrayOfArrayCopy =  []
    arrayOfArrayWithObject.map(arrayWithObject => {
      let arrayCopy = []
      arrayWithObject.map(object => {
        arrayCopy.push({ ...object })
      })
      arrayOfArrayCopy.push(arrayCopy)
    })
    return arrayOfArrayCopy
  },
  formatEntitiesHayson(entitiesArray) {
    const objectWithoutKey = (object, key) => {
    const {[key]: deletedKey, ...otherKeys} = object
      return otherKeys
    }
    return entitiesArray.flat().map(entity => {
        let newEntity  = {}
        Object.keys(entity).forEach(key => {
           let newValField = objectWithoutKey(entity[key], 'apiSource')
           newEntity[key] = newValField.hasOwnProperty('_kind') ? newValField : newValField.val
        })
        return newEntity
    })
  }
}

export default utils
