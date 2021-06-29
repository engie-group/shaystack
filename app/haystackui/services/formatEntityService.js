import { utils, API_COLORS } from './index.js'

const formatEntityService = {
  formatIdEntity: id => {
    return id.split(' ')[0].substring(2)
  },
  isRef: value => {
    return value.substring(0,2) === 'r:'
  },
  isNumber: string => {
    return Boolean(Number(string))
  },
  isEntityFromSource: (entitiesFromAllSource, entityId) => {
    let isEntityFromSource = false
    entitiesFromAllSource.map(entities => {
      entities.map(entity => {
        if(entity.id.val === entityId || entity.id.val.split(' ')[0] === entityId.split(' ')[0]) isEntityFromSource = true
      })
    })
    return isEntityFromSource
  },
  formatEntityName: entity => {
    const id = entity.id.val
    const entityName = id.substring(2).split(' ')
    if(entityName.length === 1) {
      if(entity.dis) return entity.dis.val.substring(2)
      return `@${entityName[0]}`
    }
    entityName.shift()
    return entityName.join(' ')
  },
  idToNameEntity: entitiesfromAllSource => {
    let mapEntityIdToEntityName = {}
    entitiesfromAllSource.map(entities => {
      entities.map(entity => {
        const entityId = formatEntityService.formatIdEntity(entity.id.val)
        const entityName = formatEntityService.formatEntityName(entity)
        mapEntityIdToEntityName[entityId] = entityName
      })
    })
    return mapEntityIdToEntityName
  },
  addApiSourceInformationToEntity: (entities, apiNumber) => {
    entities.map(entity => {
      Object.keys(entity).map(key => {
        if (typeof entity[key] === 'string') {
          const newEntityKey = { val: entity[key], apiSource: apiNumber}
          entity[key] = newEntityKey
        }
        else if (typeof entity[key] === 'boolean') {
          const newEntityKey = { val: `b:${entity[key]}`, apiSource: apiNumber}
          entity[key] = newEntityKey
        }
        return entity
      })
    })
    return entities
  },
  addApiSourceInformation: (entitiesFromAllSource) => {
    entitiesFromAllSource.slice().map((entities, index) => {
      entities.map(entity => {
        Object.keys(entity).map(key => {
          if (typeof entity[key] === 'string') {
            const newEntityKey = { val: entity[key], apiSource: index}
            entity[key] = newEntityKey
          }
        })
        return key
      })
      return entity
    })
    return entitiesFromAllSource
  },
  groupAllEntitiesById: entitiesFromAllSources => {
    let entitiesFromAllSourceCopy = utils.copyArrayOfArrayWithObject(entitiesFromAllSources)
    let initialEntities = entitiesFromAllSourceCopy.shift()
    return entitiesFromAllSourceCopy.reduce((acc, entities) => formatEntityService.groupTwoEntitiesById(acc, entities), initialEntities)
  },
  groupTwoEntitiesById: (entitiesFromFirstSource, entitiesFromSecondSource) => {
    const mergeEntities = []
    entitiesFromFirstSource.map(entityFromFirstSource => {
      const idFromSource = formatEntityService.formatIdEntity(entityFromFirstSource.id.val)
      entitiesFromSecondSource.map(entityFromSecondSource => {  // Refactor complexity
        const idFromSecondSource = formatEntityService.formatIdEntity(entityFromSecondSource.id.val)
        if (idFromSource === idFromSecondSource) {
          const keysWithSameValues = utils.findSimilarObjectsKeyWithSameValues(
            entityFromFirstSource,
            entityFromSecondSource
          )
          keysWithSameValues.map(key => {
            if(key === 'his') {
              if (typeof entityFromFirstSource[key].apiSource !== 'object') {
                const newApiSourceValue = []
                newApiSourceValue.push(entityFromFirstSource[key].apiSource)
                newApiSourceValue.push(entityFromSecondSource[key].apiSource)
                delete entityFromSecondSource[key]
                entityFromFirstSource[key].apiSource = newApiSourceValue
              }
              else {
                if (!entityFromFirstSource[key].apiSource.find(apiSource => apiSource === entityFromSecondSource[key].apiSource)) {
                  entityFromFirstSource[key].apiSource.push(entityFromSecondSource[key].apiSource)
                  delete entityFromSecondSource[key]
                }
                else delete entityFromSecondSource[key]
              }
            }
            else entityFromSecondSource[key] = entityFromFirstSource[key]
          })
          entityFromSecondSource['id'] = entityFromFirstSource['id']
          entityFromSecondSource = utils.getKeyAlreadyDuplicated(entityFromFirstSource, entityFromSecondSource)
          const keysWithDifferentValues = utils.findSimilarObjectsKeyWithDifferentsValues(
            entityFromFirstSource,
            entityFromSecondSource
          )
          keysWithDifferentValues.map(key => {
            if(key === 'id') {
              entityFromSecondSource[key] = entityFromFirstSource[key]
            }
            else {
              entityFromFirstSource = utils.renameObjectKey(entityFromFirstSource, key, `${key}_${entityFromFirstSource[key].apiSource}`)
              entityFromSecondSource = utils.renameObjectKey(entityFromSecondSource, key, `${key}_${entityFromSecondSource[key].apiSource}`)
              delete entityFromFirstSource[key]
              delete entityFromSecondSource[key]
            }
          })
          mergeEntities.push({ ...entityFromFirstSource, ...entityFromSecondSource })
          entitiesFromSecondSource = entitiesFromSecondSource.filter(entity => formatEntityService.formatIdEntity(entity.id.val) !== idFromSource)
          entitiesFromFirstSource = entitiesFromFirstSource.filter(entity => formatEntityService.formatIdEntity(entity.id.val) !== idFromSource)
        }
      })
    })
    return mergeEntities.concat(entitiesFromFirstSource.concat(entitiesFromSecondSource))
  },
  getLinkBetweenEntities: (entitiesFromAllSource) => {
    const colors = { fromSource: API_COLORS, outFromSource: '#c1e1ec' }
    const radiusNode = { fromSource: 7, outFromSource: 5 }
    const entitiesLink = []
    const entitiesNameToEntitiesId = formatEntityService.idToNameEntity(entitiesFromAllSource)
    const colorsLinkOutFromSource = []
    entitiesFromAllSource.map(entities => {
      entities.map( entity => {
        const formatedEntityId = formatEntityService.formatIdEntity(entity.id.val)
        Object.keys(entity).map(key => {
          if(typeof entity[key] !== 'boolean') {
            if(formatEntityService.isRef(entity[key].val) && key !== 'id') {
              const formatedEntityIdLinked = formatEntityService.formatIdEntity(entity[key].val)
              const formatedLink = [formatedEntityId, formatedEntityIdLinked, key]
              if(!formatEntityService.isEntityFromSource(entitiesFromAllSource, entity[key].val)) {
                colorsLinkOutFromSource.push({ id: formatedEntityIdLinked, color: colors.outFromSource, marker: { radius: radiusNode.outFromSource } })
              }
              else colorsLinkOutFromSource.push({ id: formatedEntityIdLinked, color: colors.fromSource[entity.id.apiSource - 1], marker: { radius: radiusNode.fromSource } })
              entitiesLink.push(formatedLink)
            }
          }
          return key
        })
        colorsLinkOutFromSource.push({
            id: formatedEntityId, color: colors.fromSource[entity.id.apiSource - 1],
            dis: entity.dis ? entity.dis.val.substring(2) : formatedEntityId,
            marker: { radius:
                radiusNode.fromSource + formatEntityService.getConnectionOccurence(formatedEntityId, entitiesLink) },
            name: entitiesNameToEntitiesId[formatedEntityId]
            }
          )
      })
    })
    return [entitiesLink, colorsLinkOutFromSource, entitiesNameToEntitiesId]
  },
    reajustEntitiespiSource(entities, indexApiDeleted) {
    const entitiesCopy = entities.slice()
    let entitiesReajusted = []
    entitiesCopy.map((apiEntities, index) => {
      if (index < indexApiDeleted) entitiesReajusted.push(apiEntities)
      else {
        let apiEntitiesReajusted = []
        apiEntities.map(entity => {
          const entityReajusted = {}
          Object.keys(entity).map(key => {
            entityReajusted[key] = { val: entity[key].val, apiSource: entity[key].apiSource - 1}
          })
          apiEntitiesReajusted.push(entityReajusted)
        })
        entitiesReajusted.push(apiEntitiesReajusted)
      }
    })
    return entitiesReajusted
  },
  getConnectionOccurence(entityId, entitiesLink) {
    return entitiesLink.find(entityLink => entityLink.includes(entityId)) ?
      entitiesLink.find(entityLink => entityLink.includes(entityId)).length :
      0
  },
  reajustHistoriesApiSource(histories, indexApiDeleted) {
    const historiesCopy = histories.slice()
    let historiesReajusted = []
    historiesCopy.map((apiHistories, index) => {
      if (index < indexApiDeleted) historiesReajusted.push(apiHistories)
      else {
        let apiHistoriesReajusted = {}
        Object.keys(apiHistories).map(historyId => {
          const historyEntity = []
          apiHistories[historyId].map(pointHistoryId => {
            historyEntity.push({ val: pointHistoryId.val, ts: pointHistoryId.ts, apiSource: pointHistoryId.apiSource - 1 })
          })
          apiHistoriesReajusted[historyId] = historyEntity
        })
        historiesReajusted.push(apiHistoriesReajusted)
      }
    })
    return historiesReajusted
  }
}

export default formatEntityService
